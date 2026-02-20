from django.test import TestCase
from django.contrib.auth.models import User
from accounts.models import Profile
from classrooms.models import Subject, ClassGroup, GroupMembership
from .models import Task, Submission


class AssignmentModelTests(TestCase):
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

    def test_create_task_and_submission(self):
        t = Task.objects.create(title='Task A', description='desc', created_by=self.teacher, group=self.group)
        s = Submission.objects.create(task=t, student=self.student, content='x')
        self.assertEqual(s.task, t)
        self.assertEqual(s.student, self.student)
        self.assertFalse(s.submitted)

