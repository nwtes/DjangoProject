from django.db import models
from assignments.models import Task
from accounts.models import Profile
from django.contrib.auth.models import User

# Create your models here.

class TaskDocument(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    student = models.ForeignKey(Profile,on_delete=models.CASCADE)
    content = models.TextField(default= "",blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        unique_together = ("task", "student")

    def __str__(self):
        return f'{self.task.title} by {self.student}'

class TaskDocumentVersion(models.Model):
    document = models.ForeignKey(TaskDocument,on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add = True)
    author = models.ForeignKey(Profile,on_delete=models.CASCADE)

class LiveTaskSession(models.Model):
    document = models.ForeignKey(TaskDocument,on_delete=models.CASCADE)
    user = models.ForeignKey(Profile,on_delete=models.CASCADE)
    cursor_pos = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user} is editing document by id {self.document.id}"

class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.body[:40]}"
