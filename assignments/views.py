from django.shortcuts import render, get_object_or_404 , redirect
from .models import Task,Submission

# Create your views here.

def student_task_view(request,task_id):
    student = request.user.profile
    task = get_object_or_404(Task,id = task_id)

    if request.method == "POST":
        message = request.POST.get("message")
        Submission.objects.create(
            task = task,
            student=student,
            content = message
        )
        return redirect("student_dashboard")
    return render(request,"tasks/task.html" , {"task" : task})