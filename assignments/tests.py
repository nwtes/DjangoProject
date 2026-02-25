from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from classrooms.models import Subject, ClassGroup, GroupMembership
from .models import Task, Submission, FinalSubmission
from editor.models import TaskDocument
import json


class TaskModelTests(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(username='t2', password='pass')
        self.teacher = self.teacher_user.profile
        self.teacher.role = 'teacher'
        self.teacher.save()
        self.student_user = User.objects.create_user(username='s2', password='pass')
        self.student = self.student_user.profile
        self.student.role = 'student'
        self.student.save()
        self.subject = Subject.objects.create(name='Sci', teacher=self.teacher)
        self.group = ClassGroup.objects.create(name='G2', subject=self.subject)
        GroupMembership.objects.create(student=self.student, group=self.group)

    def test_create_task(self):
        t = Task.objects.create(title='Task A', description='desc', created_by=self.teacher, group=self.group)
        self.assertEqual(str(t), f"Task Task A that are created by {self.teacher}")
        self.assertFalse(t.is_live)

    def test_task_default_type_is_text(self):
        t = Task.objects.create(title='T', description='d', created_by=self.teacher, group=self.group)
        self.assertEqual(t.task_type, 'text')

    def test_task_python_type(self):
        t = Task.objects.create(title='PyTask', description='d', created_by=self.teacher, group=self.group, task_type='python')
        self.assertEqual(t.task_type, 'python')

    def test_task_starter_code_optional(self):
        t = Task.objects.create(title='T', description='d', created_by=self.teacher, group=self.group)
        self.assertIsNone(t.starter_code)

    def test_create_submission(self):
        t = Task.objects.create(title='Task A', description='desc', created_by=self.teacher, group=self.group)
        s = Submission.objects.create(task=t, student=self.student, content='x')
        self.assertEqual(s.task, t)
        self.assertEqual(s.student, self.student)
        self.assertFalse(s.submitted)

    def test_submission_unique_per_student_task(self):
        t = Task.objects.create(title='Task B', description='desc', created_by=self.teacher, group=self.group)
        Submission.objects.create(task=t, student=self.student, content='a')
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Submission.objects.create(task=t, student=self.student, content='b')

    def test_final_submission_str(self):
        t = Task.objects.create(title='FTask', description='d', created_by=self.teacher, group=self.group)
        s = Submission.objects.create(task=t, student=self.student, content='c')
        fs = FinalSubmission.objects.create(submission=s)
        self.assertIn(str(self.student), str(fs))


class AssignmentViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = User.objects.create_user(username='tv', password='pass')
        self.teacher = self.teacher_user.profile
        self.teacher.role = 'teacher'
        self.teacher.save()
        self.student_user = User.objects.create_user(username='sv', password='pass')
        self.student = self.student_user.profile
        self.student.role = 'student'
        self.student.save()
        self.subject = Subject.objects.create(name='Art', teacher=self.teacher)
        self.group = ClassGroup.objects.create(name='GA', subject=self.subject)
        GroupMembership.objects.create(student=self.student, group=self.group)
        self.task = Task.objects.create(title='ViewTask', description='d', created_by=self.teacher, group=self.group)

    def test_student_task_view_requires_login(self):
        r = self.client.get(reverse('task', kwargs={'task_id': self.task.id}))
        self.assertEqual(r.status_code, 302)

    def test_student_task_view_loads(self):
        self.client.login(username='sv', password='pass')
        r = self.client.get(reverse('task', kwargs={'task_id': self.task.id}))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'ViewTask')

    def test_student_task_view_creates_document_and_submission(self):
        self.client.login(username='sv', password='pass')
        self.client.get(reverse('task', kwargs={'task_id': self.task.id}))
        self.assertTrue(TaskDocument.objects.filter(task=self.task, student=self.student).exists())
        self.assertTrue(Submission.objects.filter(task=self.task, student=self.student).exists())

    def test_autosave_saves_content(self):
        self.client.login(username='sv', password='pass')
        self.client.get(reverse('task', kwargs={'task_id': self.task.id}))
        r = self.client.post(
            reverse('autosave', kwargs={'task_id': self.task.id}),
            data=json.dumps({'content': 'my code'}),
            content_type='application/json'
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['saved'])
        doc = TaskDocument.objects.get(task=self.task, student=self.student)
        self.assertEqual(doc.content, 'my code')

    def test_autosave_rejects_non_post(self):
        self.client.login(username='sv', password='pass')
        r = self.client.get(reverse('autosave', kwargs={'task_id': self.task.id}))
        self.assertEqual(r.status_code, 400)

    def test_submit_task_creates_final_submission(self):
        self.client.login(username='sv', password='pass')
        Submission.objects.get_or_create(task=self.task, student=self.student, defaults={'content': 'x'})
        self.client.post(reverse('submit', kwargs={'task_id': self.task.id}))
        self.assertTrue(FinalSubmission.objects.filter(submission__task=self.task, submission__student=self.student).exists())

    def test_student_tasks_list_view(self):
        self.client.login(username='sv', password='pass')
        r = self.client.get(reverse('student_tasks'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'ViewTask')

    def test_student_tasks_filter_by_group(self):
        self.client.login(username='sv', password='pass')
        r = self.client.get(reverse('student_tasks'), {'group': self.group.id})
        self.assertEqual(r.status_code, 200)

    def test_teacher_tasks_list_view(self):
        self.client.login(username='tv', password='pass')
        r = self.client.get(reverse('teacher_tasks'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'ViewTask')

    def test_grading_view_get(self):
        sub = Submission.objects.create(task=self.task, student=self.student, content='x')
        self.client.login(username='tv', password='pass')
        r = self.client.get(reverse('submission', kwargs={'submission_id': sub.id}))
        self.assertEqual(r.status_code, 200)

    def test_grading_view_post_grades_submission(self):
        sub = Submission.objects.create(task=self.task, student=self.student, content='x')
        self.client.login(username='tv', password='pass')
        self.client.post(reverse('submission', kwargs={'submission_id': sub.id}), {
            'grade': 85,
            'comment': 'Good work'
        })
        sub.refresh_from_db()
        self.assertEqual(sub.grade, 85)
        self.assertEqual(sub.comment, 'Good work')

    def test_student_submission_view(self):
        sub = Submission.objects.create(task=self.task, student=self.student, content='x', grade=90)
        self.client.login(username='sv', password='pass')
        r = self.client.get(reverse('student_submission', kwargs={'submission_id': sub.id}))
        self.assertEqual(r.status_code, 200)
