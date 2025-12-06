from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404 , redirect,reverse
from .models import Task,Submission,FinalSubmission
from .forms import GradingForm
from django.http import JsonResponse
from django.middleware.csrf import get_token
import json
# Create your views here.

def student_task_view(request,task_id):
    student = request.user.profile
    task = get_object_or_404(Task,id = task_id)
    autosave_url  = reverse("autosave", args=(task_id,))
    csrf_token = get_token(request)
    submission, created = Submission.objects.get_or_create(
        task=task,
        student=student,
        defaults={"content": ""}  # empty initial content
    )
    context = {
        'initial_content': 'loading',
        'autosave_url' : autosave_url,
        'task': task,
        'csrf_token':csrf_token,
        'submission': submission
    }

    if request.method == "POST":
        message = request.POST.get("message")
        Submission.objects.create(
            task = task,
            student=student,
            content = message
        )
        return redirect("student_dashboard")
    return render(request,"tasks/task.html" , context)

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

@login_required
def autosave_task(request, task_id):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content", "")
        task = Task.objects.get(id=task_id)
        submission , created = Submission.objects.get_or_create(
            task = task,student = request.user.profile
        )
        submission.content = content
        submission.save()
        return JsonResponse({"saved_at": "Saved!"})
    return JsonResponse({"error": "Invalid request"}, status=400)


def submit_task(request,task_id):
    student = request.user.profile
    task = get_object_or_404(Task,id = task_id)

    submission = get_object_or_404(Submission,task = task,student = student)

    final_submission ,created = FinalSubmission.objects.get_or_create(
        submission = submission,
    )
    task.submitted = True
    task.save()
    
    if created:
        pass
    return redirect("student_dashboard")