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
    group = models.ForeignKey(ClassGroup,on_delete = models.CASCADE,related_name="task")

    def clean(self):

        '''if not self.created_by or not self.group:
            return

        if self.created_by != self.group.subject.teacher:
            raise ValidationError("You cannot create tasks for groups you dont teach")'''

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
    submitted = models.BooleanField(default = False)
    grade = models.IntegerField(null = True,blank = True)
    comment = models.TextField(null = True,blank = True)

    class Meta:
        unique_together = ('task','student')

class FinalSubmission(models.Model):
    submission = models.OneToOneField('Submission',on_delete = models.CASCADE,null=True,blank=True)
    submitted_at = models.DateTimeField(auto_now_add = True)
    def __str__(self):
        return f"{self.submission.student} - {self.submission.task}"