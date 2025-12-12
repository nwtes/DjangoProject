import json
import os
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from . import models
from django.conf import settings
import redis.asyncio as aioredis

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")


class UpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]
        self.group_name = f"task_{self.task_id}"

        if settings.DEBUG:
            self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        else:
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
        else:
            try:
                watching_key = f"watching:{self.task_id}"
                teacher_id = str(self.user.id)
                prev = await self.redis.hget(watching_key, teacher_id)
                if prev is not None:
                    await self.redis.hdel(watching_key, teacher_id)
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "teacher_watch_event",
                            "action": "stop",
                            "teacher_id": self.user.id,
                            "teacher_username": self.user.username,
                            "student_id": int(prev)
                        }
                    )
            except Exception:
                pass

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_user_role(self):
        return self.user.profile.role

    async def add_student(self):
        try:
            await self.redis.hset(f"students:{self.task_id}", self.user.id, json.dumps({"username": self.user.username, "last_seen": str(int(time.time() * 1000))}))
        except Exception:
            try:
                await self.redis.hset(f"students:{self.task_id}", self.user.id, self.user.username)
            except Exception:
                pass

    async def delete_student(self):
        try:
            await self.redis.hdel(f"students:{self.task_id}", self.user.id)
        except Exception:
            pass

    @database_sync_to_async
    def _get_documents_map(self, task_id):
        docs = models.TaskDocument.objects.filter(task_id=task_id).values("student_id", "content")
        return {d["student_id"]: d["content"] for d in docs}

    async def get_students(self):
        try:
            data = await self.redis.hgetall(f"students:{self.task_id}")
        except Exception:
            data = {}
        docs_map = await database_sync_to_async(self._get_documents_map_sync)(self.task_id)
        students = []
        for uid, value in data.items():
            try:
                sid = int(uid)
            except Exception:
                continue
            username = None
            last_seen = None
            try:
                parsed = json.loads(value)
                username = parsed.get('username')
                last_seen = parsed.get('last_seen')
            except Exception:
                username = value
            students.append({
                "id": sid,
                "username": username,
                "content": docs_map.get(sid, ""),
                "last_seen": last_seen
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
        if not text_data:
            return
        if len(text_data) > 300_000:
            return
        try:
            data = json.loads(text_data)
        except Exception:
            return

        if data.get('type') == 'help_request':
            student_id = self.user.id
            payload = {
                'student_id': student_id,
                'username': self.user.username,
                'note': data.get('note', ''),
                'timestamp': int(time.time() * 1000)
            }
            await self.channel_layer.group_send(self.group_name, { 'type': 'send_help_request', **payload })
            return

        if data.get('type') == 'watch' or data.get('type') == 'watch_stop':
            role = await self.get_user_role()
            if role != 'teacher':
                return
            teacher_id = str(self.user.id)
            watching_key = f"watching:{self.task_id}"
            try:
                if data.get('type') == 'watch':
                    target = data.get('student_id')
                    if target is None:
                        return
                    await self.redis.hset(watching_key, teacher_id, str(target))
                    await self.channel_layer.group_send(
                        self.group_name,
                        {
                            "type": "teacher_watch_event",
                            "action": "start",
                            "teacher_id": self.user.id,
                            "teacher_username": self.user.username,
                            "student_id": int(target)
                        }
                    )
                else:
                    prev = await self.redis.hget(watching_key, teacher_id)
                    await self.redis.hdel(watching_key, teacher_id)
                    if prev is not None:
                        await self.channel_layer.group_send(
                            self.group_name,
                            {
                                "type": "teacher_watch_event",
                                "action": "stop",
                                "teacher_id": self.user.id,
                                "teacher_username": self.user.username,
                                "student_id": int(prev)
                            }
                        )
            except Exception:
                pass
            return

        role = await self.get_user_role()

        if role == "student":
            student_id = self.user.id
            content = data.get("content", "")
            await database_sync_to_async(self._save_document_sync)(student_id, content)
            try:
                await self.redis.hset(f"students:{self.task_id}", self.user.id, json.dumps({"username": self.user.username, "last_seen": str(int(time.time() * 1000))}))
            except Exception:
                pass
        else:
            student_id = data.get("student_id")
            content = data.get("content", "")
            if not student_id:
                return
            await database_sync_to_async(self._save_document_sync)(student_id, content)

        seq = data.get('seq') if isinstance(data.get('seq'), int) else int(time.time() * 1000)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_change",
                "student_id": student_id,
                "content": content,
                "seq": seq
            }
        )

    async def send_help_request(self, event):
        payload = {
            'type': 'help_request',
            'student_id': event.get('student_id'),
            'username': event.get('username'),
            'note': event.get('note', ''),
            'timestamp': event.get('timestamp')
        }
        await self.send(text_data=json.dumps(payload))

    async def teacher_watch_event(self, event):
        payload = {
            'type': 'teacher_watch',
            'action': event.get('action'),
            'teacher_id': event.get('teacher_id'),
            'teacher_username': event.get('teacher_username'),
            'student_id': event.get('student_id')
        }
        await self.send(text_data=json.dumps(payload))

    async def broadcast_change(self, event):
        await self.send(text_data=json.dumps({
            "type": "broadcast_change",
            "student_id": event["student_id"],
            "content": event["content"],
            "seq": event.get('seq')
        }))

    def _get_documents_map_sync(self, task_id):
        docs = models.TaskDocument.objects.filter(task_id=task_id).values("student_id", "content")
        return {d["student_id"]: d["content"] for d in docs}

    def _save_document_sync(self, student_id, content):
        doc, _ = models.TaskDocument.objects.get_or_create(
            task_id=self.task_id,
            student_id=student_id
        )
        doc.content = content
        doc.save()