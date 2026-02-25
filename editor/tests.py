from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import Profile
from classrooms.models import Subject, ClassGroup, GroupMembership
from assignments.models import Task, Submission
from .models import TaskDocument, TaskDocumentVersion, DirectMessage


class TaskDocumentModelTests(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(username='edteacher', password='pass')
        self.teacher = self.teacher_user.profile
        self.teacher.role = 'teacher'
        self.teacher.save()
        self.student_user = User.objects.create_user(username='edstudent', password='pass')
        self.student = self.student_user.profile
        self.student.role = 'student'
        self.student.save()
        self.subject = Subject.objects.create(name='CS', teacher=self.teacher)
        self.group = ClassGroup.objects.create(name='CS1', subject=self.subject)
        GroupMembership.objects.create(student=self.student, group=self.group)
        self.task = Task.objects.create(title='Code', description='d', created_by=self.teacher, group=self.group)

    def test_task_document_created(self):
        doc = TaskDocument.objects.create(task=self.task, student=self.student, content='print(1)')
        self.assertEqual(doc.content, 'print(1)')
        self.assertIn('Code', str(doc))

    def test_task_document_unique_per_student_task(self):
        TaskDocument.objects.create(task=self.task, student=self.student)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TaskDocument.objects.create(task=self.task, student=self.student)

    def test_task_document_default_content_empty(self):
        doc = TaskDocument.objects.create(task=self.task, student=self.student)
        self.assertEqual(doc.content, '')

    def test_task_document_version_created(self):
        doc = TaskDocument.objects.create(task=self.task, student=self.student, content='v1')
        version = TaskDocumentVersion.objects.create(document=doc, content='v1', author=self.student)
        self.assertEqual(version.content, 'v1')
        self.assertEqual(version.author, self.student)

    def test_multiple_versions_per_document(self):
        doc = TaskDocument.objects.create(task=self.task, student=self.student, content='a')
        TaskDocumentVersion.objects.create(document=doc, content='a', author=self.student)
        TaskDocumentVersion.objects.create(document=doc, content='b', author=self.student)
        self.assertEqual(TaskDocumentVersion.objects.filter(document=doc).count(), 2)


class DirectMessageModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='dm1', password='pass')
        self.user2 = User.objects.create_user(username='dm2', password='pass')

    def test_create_message(self):
        msg = DirectMessage.objects.create(sender=self.user1, recipient=self.user2, body='Hello')
        self.assertEqual(msg.body, 'Hello')
        self.assertFalse(msg.read)
        self.assertIn('dm1', str(msg))

    def test_message_ordered_by_sent_at(self):
        DirectMessage.objects.create(sender=self.user1, recipient=self.user2, body='First')
        DirectMessage.objects.create(sender=self.user2, recipient=self.user1, body='Second')
        msgs = list(DirectMessage.objects.all())
        self.assertEqual(msgs[0].body, 'First')
        self.assertEqual(msgs[1].body, 'Second')

    def test_mark_read(self):
        msg = DirectMessage.objects.create(sender=self.user1, recipient=self.user2, body='Hi')
        msg.read = True
        msg.save()
        msg.refresh_from_db()
        self.assertTrue(msg.read)
