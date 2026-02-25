from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile


class ProfileSignalTests(TestCase):
    def test_profile_created_on_user_creation(self):
        u = User.objects.create_user(username='alice', password='pass')
        self.assertTrue(hasattr(u, 'profile'))
        self.assertIsInstance(u.profile, Profile)

    def test_profile_default_role_is_student(self):
        u = User.objects.create_user(username='bob', password='pass')
        self.assertEqual(u.profile.role, 'student')

    def test_profile_str(self):
        u = User.objects.create_user(username='charlie', password='pass')
        self.assertEqual(str(u.profile), 'charlie')

    def test_profile_role_can_be_set_to_teacher(self):
        u = User.objects.create_user(username='diana', password='pass')
        u.profile.role = 'teacher'
        u.profile.save()
        u.refresh_from_db()
        self.assertEqual(u.profile.role, 'teacher')

    def test_profile_display_name_optional(self):
        u = User.objects.create_user(username='eve', password='pass')
        self.assertIsNone(u.profile.display_name)
        u.profile.display_name = 'Eve Smith'
        u.profile.save()
        self.assertEqual(u.profile.display_name, 'Eve Smith')

    def test_profile_bio_optional(self):
        u = User.objects.create_user(username='frank', password='pass')
        u.profile.bio = 'A short bio.'
        u.profile.save()
        self.assertEqual(u.profile.bio, 'A short bio.')


class RegistrationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('register')

    def test_register_page_loads(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_register_creates_student_user(self):
        r = self.client.post(self.url, {
            'username': 'newstudent',
            'email': 'student@test.com',
            'password': 'testpass123',
            'role': 'student',
        })
        self.assertEqual(r.status_code, 302)
        u = User.objects.get(username='newstudent')
        self.assertEqual(u.profile.role, 'student')

    def test_register_creates_teacher_user(self):
        self.client.post(self.url, {
            'username': 'newteacher',
            'email': 'teacher@test.com',
            'password': 'testpass123',
            'role': 'teacher',
        })
        u = User.objects.get(username='newteacher')
        self.assertEqual(u.profile.role, 'teacher')

    def test_register_invalid_missing_username(self):
        r = self.client.post(self.url, {
            'username': '',
            'password': 'testpass123',
            'role': 'student',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='').exists())


class LoginRedirectTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = User.objects.create_user(username='tlogin', password='pass')
        self.teacher_user.profile.role = 'teacher'
        self.teacher_user.profile.save()
        self.student_user = User.objects.create_user(username='slogin', password='pass')

    def test_teacher_redirected_to_teacher_dashboard(self):
        r = self.client.post(reverse('login'), {'username': 'tlogin', 'password': 'pass'})
        self.assertRedirects(r, '/teacher/dashboard', fetch_redirect_response=False)

    def test_student_redirected_to_student_dashboard(self):
        r = self.client.post(reverse('login'), {'username': 'slogin', 'password': 'pass'})
        self.assertRedirects(r, '/student/dashboard', fetch_redirect_response=False)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='profuser', password='pass')

    def test_profile_requires_login(self):
        r = self.client.get(reverse('profile'))
        self.assertEqual(r.status_code, 302)

    def test_profile_loads_when_logged_in(self):
        self.client.login(username='profuser', password='pass')
        r = self.client.get(reverse('profile'))
        self.assertEqual(r.status_code, 200)

    def test_edit_profile_get(self):
        self.client.login(username='profuser', password='pass')
        r = self.client.get(reverse('edit_profile'))
        self.assertEqual(r.status_code, 200)

    def test_edit_profile_post_updates_display_name(self):
        self.client.login(username='profuser', password='pass')
        self.client.post(reverse('edit_profile'), {
            'display_name': 'Updated Name',
            'bio': '',
            'phone': '',
        })
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, 'Updated Name')
