import json
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from . import models
import redis.asyncio as aioredis

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")


class UpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]
        self.group_name = f"task_{self.task_id}"

        self.redis = aioredis.from_url(f"{REDIS_URL}?ssl_cert_reqs=none", decode_responses=True)


        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        if await self.get_user_role() == "student":
            await self.add_student()
            await self.broadcast_students_list()

    async def disconnect(self, close_code):
        role = await self.get_user_role()
        if role == "student":
            await self.delete_student()
            await self.broadcast_students_list()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_user_role(self):
        return self.user.profile.role

    async def add_student(self):
        await self.redis.hset(f"students:{self.task_id}", self.user.id, self.user.username)

    async def delete_student(self):
        await self.redis.hdel(f"students:{self.task_id}", self.user.id)

    @database_sync_to_async
    def _get_documents_map(self, task_id):
        docs = models.TaskDocument.objects.filter(task_id=task_id).values("student_id", "content")
        return {d["student_id"]: d["content"] for d in docs}

    async def get_students(self):
        data = await self.redis.hgetall(f"students:{self.task_id}")
        docs_map = await self._get_documents_map(self.task_id)
        students = []
        for uid, username in data.items():
            sid = int(uid)
            students.append({
                "id": sid,
                "username": username,
                "content": docs_map.get(sid, "")
            })
        return students

    async def broadcast_students_list(self):
        students = await self.get_students()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_students_list",
                "students": students
            }
        )

    async def send_students_list(self, event):
        await self.send(text_data=json.dumps({
            "type": "student_list",
            "students": event["students"]
        }))

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        role = await self.get_user_role()


        if role == "student":
            student_id = self.user.id
            content = data.get("content")

            self.save_document(student_id, content)
        else:

            student_id = data.get("student_id")
            content = data.get("content")

            self.save_document(student_id, content)


        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_change",
                "student_id": student_id,
                "content": content
            }
        )

    async def broadcast_change(self, event):
        await self.send(text_data=json.dumps({
            "type": "broadcast_change",
            "student_id": event["student_id"],
            "content": event["content"]
        }))

    @database_sync_to_async
    def save_document(self, student_id, content):
        doc, _ = models.TaskDocument.objects.get_or_create(
            task_id=self.task_id,
            student_id=student_id
        )
        doc.content = content
        doc.save()