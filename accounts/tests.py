from django.test import TestCase
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
