from django.core.exceptions import ValidationError
from django.db import models
from accounts.models import Profile
from classrooms.models import ClassGroup
# Create your models here.

class Task(models.Model):
    title = models.CharField(max_length= 64)
    description = models.TextField()
    created_by = models.ForeignKey(
        Profile,
        on_delete = models.CASCADE,
        limit_choices_to = {"role" : "teacher"},
        related_name = "tasks"
    )
    group = models.ForeignKey(ClassGroup,on_delete = models.CASCADE)

    def clean(self):
        if self.created_by != self.group.subject.teacher:
            raise ValidationError("You cannot create tasks for groups yo dont teach")

    def __str__(self):
        return f"Task {self.title} that are created by {self.created_by}"

class Submission(models.Model):
    task = models.ForeignKey(Task,on_delete = models.CASCADE)
    student = models.ForeignKey(
        Profile,
        on_delete = models.CASCADE,
        limit_choices_to = {"role" : "student"},
        related_name = "submission"
    )
    content = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add = True)
    grade = models.IntegerField(null = True,blank = True)
    comment = models.TextField(null = True,blank = True)

    class Meta:
        unique_together = ('task','student')