from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
from .models import Subject, ClassGroup, GroupMembership, Announcement


class ClassroomModelTests(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(username='cteacher', password='pass')
        self.teacher = self.teacher_user.profile
        self.teacher.role = 'teacher'
        self.teacher.save()
        self.student_user = User.objects.create_user(username='cstudent', password='pass')
        self.student = self.student_user.profile
        self.student.role = 'student'
        self.student.save()

    def test_subject_str(self):
        s = Subject.objects.create(name='History', teacher=self.teacher)
        self.assertEqual(str(s), 'History')

    def test_classgroup_str(self):
        s = Subject.objects.create(name='Bio', teacher=self.teacher)
        g = ClassGroup.objects.create(name='BioGroup', subject=s)
        self.assertEqual(str(g), 'BioGroup')

    def test_group_membership_unique(self):
        s = Subject.objects.create(name='Chem', teacher=self.teacher)
        g = ClassGroup.objects.create(name='ChemG', subject=s)
        GroupMembership.objects.create(student=self.student, group=g)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            GroupMembership.objects.create(student=self.student, group=g)

    def test_announcement_str(self):
        s = Subject.objects.create(name='Physics', teacher=self.teacher)
        g = ClassGroup.objects.create(name='PhysG', subject=s)
        a = Announcement.objects.create(created_by=self.teacher, group=g, title='Exam', body='Study hard')
        self.assertEqual(str(a), 'Exam')

    def test_multiple_groups_per_subject(self):
        s = Subject.objects.create(name='Maths', teacher=self.teacher)
        ClassGroup.objects.create(name='M1', subject=s)
        ClassGroup.objects.create(name='M2', subject=s)
        self.assertEqual(s.classgroup.count(), 2)

    def test_student_can_join_multiple_groups(self):
        s1 = Subject.objects.create(name='S1', teacher=self.teacher)
        s2 = Subject.objects.create(name='S2', teacher=self.teacher)
        g1 = ClassGroup.objects.create(name='G1', subject=s1)
        g2 = ClassGroup.objects.create(name='G2', subject=s2)
        GroupMembership.objects.create(student=self.student, group=g1)
        GroupMembership.objects.create(student=self.student, group=g2)
        self.assertEqual(GroupMembership.objects.filter(student=self.student).count(), 2)


class ClassroomViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = User.objects.create_user(username='cvteacher', password='pass')
        self.teacher = self.teacher_user.profile
        self.teacher.role = 'teacher'
        self.teacher.save()
        self.subject = Subject.objects.create(name='Art', teacher=self.teacher)
        self.group = ClassGroup.objects.create(name='ArtG', subject=self.subject)

    def test_create_announcement_requires_login(self):
        r = self.client.get(reverse('create_announcement'))
        self.assertEqual(r.status_code, 302)

    def test_create_announcement_get(self):
        self.client.login(username='cvteacher', password='pass')
        r = self.client.get(reverse('create_announcement'))
        self.assertEqual(r.status_code, 200)

    def test_create_announcement_post(self):
        self.client.login(username='cvteacher', password='pass')
        self.client.post(reverse('create_announcement'), {
            'title': 'New Announcement',
            'body': 'Important message',
            'group': self.group.id,
        })
        self.assertTrue(Announcement.objects.filter(title='New Announcement').exists())
