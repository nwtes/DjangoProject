from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Exists, Subquery
from django.shortcuts import render, get_object_or_404, redirect, reverse
from .models import Task, Submission, FinalSubmission
from .forms import GradingForm
from classrooms.models import ClassGroup
from accounts.models import Profile
from django.http import JsonResponse
from django.utils import timezone
from django.middleware.csrf import get_token
from editor.models import TaskDocument, TaskDocumentVersion
from pages.decorators import role_required
import json


@login_required
@role_required('student')
def student_task_view(request, task_id):
    """Display the task editor page for a student."""
    student = request.user.profile
    task = get_object_or_404(Task, id=task_id)
    autosave_url = reverse("autosave", args=(task_id,))
    snapshot_url = reverse("snapshot", args=(task_id,))
    csrf_token = get_token(request)
    document, _ = TaskDocument.objects.get_or_create(task=task, student=student)
    submission, _ = Submission.objects.get_or_create(task=task, student=student)

    context = {
        'initial_content': document.content,
        'autosave_url': autosave_url,
        'snapshot_url': snapshot_url,
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
@role_required('student')
def live_tasks_for_student(request):
    """Return a JSON list of currently live tasks available to the student."""
    profile = request.user.profile
    tasks = Task.objects.filter(
        group__groupmembership__student=profile,
        is_live=True
    ).distinct().values('id', 'title', 'group__name')
    data = [
        {
            'id': t['id'],
            'title': t['title'],
            'group': t['group__name'] or '',
        }
        for t in tasks
    ]
    return JsonResponse({'tasks': data})


@login_required
@role_required('teacher')
def toggle_live(request, task_id):
    """Toggle the live state of a task on/off for the owning teacher."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    teacher = request.user.profile
    task = get_object_or_404(Task, id=task_id, created_by=teacher)
    task.is_live = not task.is_live
    task.save()
    return JsonResponse({'is_live': task.is_live})


@login_required
@role_required('teacher')
def submission_task_view(request, submission_id):
    """Display a submission and allow a teacher to grade it."""
    submission = get_object_or_404(Submission, id=submission_id)
    if request.method == "POST":
        form = GradingForm(request.POST)
        if form.is_valid():
            submission.grade = form.cleaned_data['grade']
            submission.comment = form.cleaned_data['comment']
            submission.save()
            messages.success(request, f"Submission graded successfully.")
            return redirect("teacher_dashboard")
    else:
        form = GradingForm()
    return render(request, "tasks/view_submission.html", {"submission": submission, "form": form})


@login_required
@role_required('student')
def student_submission_view(request, submission_id):
    """Display a graded submission to the student who owns it."""
    submission = get_object_or_404(Submission, id=submission_id)
    if submission.student != request.user.profile:
        messages.error(request, "You do not have permission to view this submission.")
        return redirect("student_dashboard")
    return render(request, "tasks/student_view_submission.html", {"submission": submission})


@login_required
def autosave_task(request, task_id):
    """Autosave the current editor content for a student's task document."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        content = data.get("content", "")
        if len(content) > 500000:
            return JsonResponse({"error": "Content too large"}, status=400)

        task = get_object_or_404(Task, id=task_id)
        student = request.user.profile

        document, _ = TaskDocument.objects.get_or_create(task=task, student=student)
        document.content = content
        document.save()

        submission, _ = Submission.objects.get_or_create(task=task, student=student)
        submission.content = content
        submission.save()

        return JsonResponse({"saved": True, "saved_at": "Saved at " + timezone.now().strftime("%H:%M:%S")})

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def snapshot_task(request, task_id):
    """Save a versioned snapshot of the current task document content."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Bad JSON"}, status=400)

    content = data.get("content", "")
    if len(content) > 500000:
        return JsonResponse({"error": "Content too large"}, status=400)

    task = get_object_or_404(Task, id=task_id)
    student = request.user.profile
    document, _ = TaskDocument.objects.get_or_create(task=task, student=student)
    document.content = content
    document.save()

    TaskDocumentVersion.objects.create(document=document, content=content, author=student)

    return JsonResponse({"saved": True, "saved_at": "Snapshot at " + timezone.now().strftime("%H:%M:%S")})


@login_required
def submit_task(request, task_id):
    """Mark a task submission as final for a student."""
    profile = request.user.profile
    if profile.role == 'teacher':
        return redirect(reverse('view_task', args=[task_id]))
    task = get_object_or_404(Task, id=task_id)
    submission = get_object_or_404(Submission, task=task, student=profile)
    FinalSubmission.objects.get_or_create(submission=submission)
    submission.submitted = True
    submission.save()
    messages.success(request, "Task submitted successfully.")
    return redirect("student_dashboard")


@login_required
@role_required('student')
def student_tasks_view(request):
    """Display the full task list for a student with filtering options."""
    student = request.user.profile
    submissions = FinalSubmission.objects.filter(submission__task=OuterRef('pk'), submission__student=student)
    grade_subquery = Submission.objects.filter(task=OuterRef('pk'), student=student).values('grade')[:1]
    graded_submissions = Submission.objects.filter(task=OuterRef("pk"), student=student, grade__isnull=False)

    tasks = (
        Task.objects
        .filter(group__groupmembership__student=student)
        .annotate(
            submission_exists=Exists(submissions),
            graded=Exists(graded_submissions),
            points=Subquery(grade_subquery)
        )
    )
    groups = ClassGroup.objects.filter(groupmembership__student=student)
    teachers = Profile.objects.filter(
        role='teacher',
        subjects__classgroup__groupmembership__student=student
    ).distinct()

    group_id = request.GET.get("group")
    teacher_id = request.GET.get("teacher")
    graded = request.GET.get("graded")
    submitted = request.GET.get("submitted")

    if group_id:
        tasks = tasks.filter(group__id=group_id)
    if teacher_id:
        tasks = tasks.filter(group__subject__teacher__id=teacher_id)
    if graded == "graded":
        tasks = tasks.filter(submission__grade__isnull=False)
    elif graded == "ungraded":
        tasks = tasks.filter(submission__grade__isnull=True)
    if submitted == "submitted":
        tasks = tasks.filter(submission__submitted=True)
    elif submitted == "unsubmitted":
        tasks = tasks.filter(submission__submitted=False)

    context = {
        'tasks': tasks,
        'groups': groups,
        'teachers': teachers
    }
    return render(request, 'students/student_tasks.html', context)


@login_required
@role_required('teacher')
def teacher_tasks_view(request):
    """Display the task list for a teacher with filtering options."""
    teacher = request.user.profile
    from django.db.models import Count, Q
    tasks = Task.objects.filter(created_by=teacher).annotate(
        student_submission_count=Count(
            'submission',
            filter=Q(submission__student__role='student'),
            distinct=True
        )
    )
    groups = ClassGroup.objects.filter(subject__teacher=teacher)

    group_id = request.GET.get('group')
    graded = request.GET.get('graded')
    submitted = request.GET.get('submitted')

    if group_id:
        tasks = tasks.filter(group__id=group_id)
    if graded == 'graded':
        tasks = tasks.filter(submission__grade__isnull=False, submission__student__role='student')
    elif graded == 'ungraded':
        tasks = tasks.filter(submission__grade__isnull=True, submission__student__role='student')
    if submitted == 'submitted':
        tasks = tasks.filter(submission__submitted=True, submission__student__role='student')
    elif submitted == 'unsubmitted':
        tasks = tasks.filter(submission__submitted=False, submission__student__role='student')

    context = {
        'tasks': tasks,
        'groups': groups
    }
    return render(request, 'teacher/teacher_tasks.html', context)
