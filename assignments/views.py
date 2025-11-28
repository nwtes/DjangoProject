from django.shortcuts import render, get_object_or_404 , redirect
from .models import Task,Submission
from .forms import GradingForm

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

def submission_task_view(request,submission_id):
    submission = get_object_or_404(Submission,id = submission_id)
    if request.method == "POST":
        form = GradingForm(request.POST)
        if form.is_valid():
            grade = form.cleaned_data['grade']
            submission.grade = grade
            comment = form.cleaned_data['comment']
            submission.comment = comment
            submission.save()
            return redirect("teacher_dashboard")
    else:
        form = GradingForm()
    return render(request,"tasks/view_submission.html",{"submission":submission,"form" : form})

def student_submission_view(request,submission_id):
    submission = get_object_or_404(Submission,id = submission_id)
    return render(request, "tasks/student_view_submission.html",{"submission" : submission})