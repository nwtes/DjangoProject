from django.db import models
from accounts.models import Profile
# Create your models here.

class Subject(models.Model):
    name = models.CharField(max_length=64)
    teacher = models.ForeignKey(Profile,on_delete=models.SET_NULL,limit_choices_to={"role" : "teacher"},related_name ="subjects",null = True)

    def __str__(self):
        return self.name

class ClassGroup(models.Model):
    name = models.CharField(max_length=64)
    subject = models.ForeignKey(Subject,on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    student = models.ForeignKey(
        Profile,
        on_delete = models.CASCADE,
        limit_choices_to = {"role" : "student"},
        related_name = "groups"
    )
    joined_at = models.DateTimeField(auto_now_add = True)
    group = models.ForeignKey(ClassGroup, on_delete= models.CASCADE)

    class Meta:
        unique_together = ('student','group')