from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from classrooms.models import Subject, ClassGroup, GroupMembership, Announcement
from assignments.models import Task


class PagesViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = User.objects.create_user(username='t1', password='pass')
        self.teacher = self.teacher_user.profile
        self.teacher.role = 'teacher'
        self.teacher.save()

        self.student_user = User.objects.create_user(username='s1', password='pass')
        self.student = self.student_user.profile
        self.student.role = 'student'
        self.student.save()

        self.subject = Subject.objects.create(name='Math', teacher=self.teacher)
        self.group = ClassGroup.objects.create(name='G1', subject=self.subject)
        GroupMembership.objects.create(student=self.student, group=self.group)

    def test_home_view_public(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 200)

    def test_student_dashboard_requires_login(self):
        r = self.client.get(reverse('student_dashboard'))
        self.assertEqual(r.status_code, 302)
        self.client.login(username='s1', password='pass')
        r = self.client.get(reverse('student_dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_teacher_dashboard_requires_teacher(self):
        self.client.login(username='s1', password='pass')
        r = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(r.status_code, 403)
        self.client.login(username='t1', password='pass')
        r = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_student_group_view_shows_announcements_and_students(self):
        Announcement.objects.create(created_by=self.teacher, group=self.group, title='Hi', body='x')
        self.client.login(username='s1', password='pass')
        r = self.client.get(reverse('groups'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Hi')
        self.assertContains(r, self.student_user.username)

    def test_teacher_can_view_task_page(self):
        t = Task.objects.create(title='T1', description='d', created_by=self.teacher, group=self.group)
        self.client.login(username='t1', password='pass')
        r = self.client.get(reverse('view_task', kwargs={'task_id': t.id}))
        self.assertEqual(r.status_code, 200)

