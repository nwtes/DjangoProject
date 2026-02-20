from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Exists, Subquery
from django.shortcuts import render, get_object_or_404 , redirect,reverse
from .models import Task,Submission,FinalSubmission
from .forms import GradingForm
from classrooms.models import ClassGroup
from accounts.models import Profile
from django.http import JsonResponse
from django.middleware.csrf import get_token
from editor.models import TaskDocument
import json


def student_task_view(request, task_id):
    student = request.user.profile
    task = get_object_or_404(Task, id=task_id)
    autosave_url = reverse("autosave", args=(task_id,))
    csrf_token = get_token(request)
    document, _ = TaskDocument.objects.get_or_create(
        task=task,
        student=student
    )
    submission, _ = Submission.objects.get_or_create(
        task=task,
        student=student,
    )

    context = {
        'initial_content': document.content,
        'autosave_url': autosave_url,
        'csrf_token': csrf_token,
        'task': task,
        'submission': submission,
        'document': document,
        'is_live': task.is_live,
        'user_role': student.role,
        'user_id': request.user.id
    }

    return render(request, "tasks/task.html", context)


@login_required
def live_tasks_for_student(request):
    user = request.user
    profile = user.profile
    tasks = Task.objects.filter(submission__submitted = True,group__groupmembership__student=profile, is_live=True).values('id','title','group__name')
    data = [{'id': t['id'], 'title': t['title'], 'group': t.get('group__name','')} for t in tasks]
    return JsonResponse({'tasks': data})


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

        task = get_object_or_404(Task, id=task_id)
        student = request.user.profile

        document, _ = TaskDocument.objects.get_or_create(
            task=task,
            student=student
        )
        document.content = content
        document.save()

        submission, _ = Submission.objects.get_or_create(
            task=task,
            student=student
        )
        submission.content = content
        submission.save()

        return JsonResponse({"saved": True})

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


def student_tasks_view(request):
    student = request.user.profile
    print("GET:", request.GET)
    submissions = FinalSubmission.objects.filter(submission__task = OuterRef('pk'),submission__student = student)
    grade_subquery = Submission.objects.filter(
        task=OuterRef('pk'),
        student=student
    ).values('grade')[:1]
    graded_submissions = Submission.objects.filter(
        task=OuterRef("pk"),
        student=student,
        grade__isnull=False
    )
    tasks = (
        Task.objects
        .filter(group__groupmembership__student=student)
        .annotate(
            submission_exists=Exists(submissions),
            graded=Exists(graded_submissions),
            points = Subquery(grade_subquery)
        )
    )
    groups = ClassGroup.objects.filter(groupmembership__student = student)
    teachers = Profile.objects.filter(
        role='teacher',
        subjects__classgroup__groupmembership__student=student
    ).distinct()

    group_id = request.GET.get("group")
    teacher_id = request.GET.get("teacher")
    graded = request.GET.get("graded")
    submitted = request.GET.get("submitted")
    if group_id:
        tasks = tasks.filter(group__id = group_id)
    if teacher_id:
        tasks = tasks.filter(group__subject__teacher__id = teacher_id)
    if graded == "graded":
        tasks = tasks.filter(submission__grade__isnull = False)
    elif graded == "ungraded":
        tasks = tasks.filter(submission__grade__isnull = True)
    if submitted == "submitted":
        tasks = tasks.filter(submission__submitted=True)
    elif submitted == "unsubmitted":
        tasks = tasks.filter(submission__submitted=False)

    context = {
        'tasks': tasks,
        'groups': groups,
        'teachers': teachers
    }

    return render(request,'students/student_tasks.html',context)


@login_required
def teacher_tasks_view(request):
    teacher = request.user.profile
    tasks = Task.objects.filter(created_by=teacher)
    groups = ClassGroup.objects.filter(subject__teacher=teacher)

    group_id = request.GET.get('group')
    graded = request.GET.get('graded')
    submitted = request.GET.get('submitted')

    if group_id:
        tasks = tasks.filter(group__id=group_id)
    if graded == 'graded':
        tasks = tasks.filter(submission__grade__isnull=False)
    elif graded == 'ungraded':
        tasks = tasks.filter(submission__grade__isnull=True)
    if submitted == 'submitted':
        tasks = tasks.filter(submission__submitted=True)
    elif submitted == 'unsubmitted':
        tasks = tasks.filter(submission__submitted=False)

    context = {
        'tasks': tasks,
        'groups': groups
    }

    return render(request,'teacher/teacher_tasks.html',context)
