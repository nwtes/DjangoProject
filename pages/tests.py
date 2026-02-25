from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from classrooms.models import Subject, ClassGroup, GroupMembership, Announcement
from assignments.models import Task, Submission


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

    def test_student_dashboard_redirects_when_not_logged_in(self):
        r = self.client.get(reverse('student_dashboard'))
        self.assertEqual(r.status_code, 302)

    def test_student_dashboard_loads_when_logged_in(self):
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

    def test_teacher_dashboard_redirects_when_not_logged_in(self):
        r = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(r.status_code, 302)

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

    def test_teacher_can_create_task_get(self):
        self.client.login(username='t1', password='pass')
        r = self.client.get(reverse('create_task'))
        self.assertEqual(r.status_code, 200)

    def test_teacher_can_create_task_post(self):
        self.client.login(username='t1', password='pass')
        r = self.client.post(reverse('create_task'), {
            'title': 'New Task',
            'description': 'Do this',
            'group': self.group.id,
            'task_type': 'text',
            'is_live': False,
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Task.objects.filter(title='New Task').exists())

    def test_student_cannot_create_task(self):
        self.client.login(username='s1', password='pass')
        r = self.client.get(reverse('create_task'))
        self.assertEqual(r.status_code, 403)

    def test_teacher_group_view_loads(self):
        self.client.login(username='t1', password='pass')
        r = self.client.get(reverse('teacher_groups'))
        self.assertEqual(r.status_code, 200)

    def test_teacher_analytics_view_loads(self):
        self.client.login(username='t1', password='pass')
        r = self.client.get(reverse('teacher_analytics'))
        self.assertEqual(r.status_code, 200)

    def test_teacher_can_edit_task(self):
        t = Task.objects.create(title='OldTitle', description='d', created_by=self.teacher, group=self.group)
        self.client.login(username='t1', password='pass')
        self.client.post(reverse('edit_task', kwargs={'task_id': t.id}), {
            'title': 'UpdatedTitle',
            'description': 'new desc',
            'group': self.group.id,
            'task_type': 'text',
            'is_live': False,
        })
        t.refresh_from_db()
        self.assertEqual(t.title, 'UpdatedTitle')

    def test_teacher_can_delete_task(self):
        t = Task.objects.create(title='DeleteMe', description='d', created_by=self.teacher, group=self.group)
        self.client.login(username='t1', password='pass')
        self.client.post(reverse('delete_task', kwargs={'task_id': t.id}))
        self.assertFalse(Task.objects.filter(id=t.id).exists())
