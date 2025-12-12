from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver



class Profile(models.Model):
    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    display_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)

    '''group = models.ForeignKey(
        ClassGroup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="students"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(role='teacher') & Q(group__isnull=True)) |
                    (Q(role='student'))
                ),
                name='teachers_cannot_have_group'
            )
        ]'''

    def __str__(self):
        return f"{self.user.username}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        try:
            instance.profile.save()
        except Exception:
            Profile.objects.get_or_create(user=instance)
