from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from classrooms.models import ClassGroup,Subject,GroupMembership,Announcement
from assignments.models import Task, Submission, FinalSubmission

from .forms import TaskCreationForm
from django.db import models
from django.db.models import Count, Avg
from .decorators import role_required
from accounts.models import Profile
# Create your views here.

def home_view(request):
    return render(request,"home.html")
@login_required
@role_required('student')
def student_dashboard_view(request):
    student = request.user.profile
    membership = GroupMembership.objects.filter(student = student)
    groups = [m.group for m in membership]
    tasks = Task.objects.filter(group__groupmembership__student=student)
    submission = Submission.objects.filter(student = student)
    graded_tasks = submission.filter(grade__isnull = False)
    assigned_tasks = submission.filter(grade__isnull = True)
    graded_task_ids = graded_tasks.values_list('task_id', flat=True)
    assigned_tasks = tasks.exclude(id__in=graded_task_ids)

    return render(request,"dashboard/student.html", {
        "groups" : groups,
        "tasks" : assigned_tasks,
        "submissions": submission,
        'graded_tasks': graded_tasks
    })
@login_required
@role_required('teacher')
def teacher_dashboard_view(request):
    teacher = request.user.profile
    subject = Subject.objects.filter(teacher=teacher)
    groups = ClassGroup.objects.filter(subject__teacher=teacher).annotate(
        student_count = Count("groupmembership", distinct=True),
        task_count = Count("task", distinct=True)
    )
    tasks = Task.objects.filter(created_by = teacher)
    submissions = FinalSubmission.objects.filter(submission__task__created_by = teacher,submission__grade__isnull = True)
    subjects = Subject.objects.filter(teacher = teacher).annotate(
        group_count = Count("classgroup"),
        task_count = Count("classgroup__task")
    )
    return render(request,"dashboard/teacher.html",{
        "subject" : subject,
        "groups" : groups,
        'tasks' : tasks,
        "subjects": subjects,
        "submissions" : submissions
    })

@role_required('teacher')
def teacher_analytics_view(request):
    teacher = request.user.profile

    # Context data for analytics
    groups = ClassGroup.objects.filter(subject__teacher=teacher)
    tasks = Task.objects.filter(created_by=teacher)
    submissions = Submission.objects.filter(task__created_by=teacher)

    total_students = GroupMembership.objects.filter(group__in=groups).count()
    avg_grade = submissions.filter(grade__isnull=False).aggregate(Avg('grade'))['grade__avg']

    # Tasks with submission counts
    task_analytics = tasks.annotate(
        submission_count=Count('submission', filter=models.Q(submission__submitted=True)),
        graded_count=Count('submission', filter=models.Q(submission__grade__isnull=False))
    )

    context = {
        "total_groups": groups.count(),
        "total_tasks": tasks.count(),
        "total_students": total_students,
        "total_submissions": submissions.filter(submitted=True).count(),
        "average_grade": round(avg_grade, 2) if avg_grade else 0,
        "task_analytics": task_analytics
    }
    return render(request, "dashboard/analytics.html", context)

@role_required('teacher')
def create_task(request):
    teacher = request.user.profile

    if request.GET.get("subject"):
        subject = request.GET.get("subject")
        allowed_groups = ClassGroup.objects.filter(subject = subject,subject__teacher=teacher)
    elif request.GET.get("group"):
        group = request.GET.get("group")
        allowed_groups = ClassGroup.objects.filter(id = group, subject__teacher=teacher)
    else:
        allowed_groups = ClassGroup.objects.filter(subject__teacher=teacher)

    if request.method == "POST":

        form = TaskCreationForm(request.POST)
        form.fields['group'].queryset = allowed_groups

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = teacher
            task.save()
            return redirect("teacher_dashboard")

    else:
        if request.GET.get("group"):
             form = TaskCreationForm(initial={'group': request.GET.get("group")})
        else:
             form = TaskCreationForm()
        form.fields['group'].queryset = allowed_groups
    return render(request,"tasks/create_task.html",{"form" : form})

def task_page_view(request, task_id):
    teacher = request.user.profile
    task = get_object_or_404(Task, id = task_id, created_by = teacher)
    submission = Submission.objects.filter(task = task)
    return render(request,'tasks/view_task.html',{"task":task,"submission" : submission})
@role_required('teacher')
def task_page_edit(request,task_id):
    teacher = request.user.profile

    task = get_object_or_404(Task, id = task_id,created_by = teacher)

    allowed_groups = ClassGroup.objects.filter(subject__teacher = teacher)

    if request.method == "POST":
        form = TaskCreationForm(request.POST, instance = task)
        form.fields['group'].queryset = allowed_groups

        if form.is_valid():
            form.save()
            return redirect("view_task",task_id = task.id)
    else:
        form = TaskCreationForm(instance = task)
        form.fields['group'].queryset = allowed_groups
    return render(request,"tasks/edit_task.html",{"form":form , "task" : task})
@role_required('teacher')
def task_page_delete(request,task_id):
    teacher = request.user.profile

    task = get_object_or_404(Task,id = task_id,created_by = teacher)

    if request.method == "POST":
        task.delete()
        return redirect("teacher_dashboard")
    return render(request,'home.html')

def student_group_view(request):
    student = request.user.profile
    group_id = request.GET.get('group_id')
    groups = ClassGroup.objects.filter(groupmembership__student=student)
    if group_id:
        current_group = get_object_or_404(ClassGroup, id=group_id)
    else:
        current_group = groups.first()
        if not current_group:
            pass
    posts = Announcement.objects.filter(group=current_group)
    students = Profile.objects.filter(
        role='student',
        groups__group=current_group
    ).distinct()
    context = {
        'current_group': current_group,
        'groups': groups,
        'students': students,
        'announcements': posts
    }
    return render(request,'students/student_view_group.html',context)
def teacher_group_view(request):
    teacher = request.user.profile
    group_id = request.GET.get('group_id')
    groups = ClassGroup.objects.filter(subject__teacher=teacher)
    if group_id:
        current_group = get_object_or_404(ClassGroup, id=group_id)
    else:
        current_group = groups.first()
    posts = Announcement.objects.filter(group=current_group) if current_group else Announcement.objects.none()
    students = Profile.objects.filter(
        role='student',
        groups__group=current_group
    ).distinct() if current_group else Profile.objects.none()
    context = {
        'current_group': current_group,
        'groups': groups,
        'students': students,
        'announcements': posts
    }
    return render(request, 'teacher/teacher_view_group.html', context)


def student_group(request,group_id):
    student = request.user.profile
    groups = ClassGroup.objects.filter(groupmembership__student=student)
    if group_id:
        current_group = get_object_or_404(ClassGroup, id=group_id)
    else:
        current_group = groups.first()
        if not current_group:
            pass
    posts = Announcement.objects.filter(group=current_group)
    students = Profile.objects.filter(
        role='student',
        groups__group=current_group
    ).distinct()
    context = {
        'current_group': current_group,
        'groups': groups,
        'students': students,
        'announcements': posts
    }
    return render(request,'students/student_view_group.html',context)


def superuser_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


@superuser_required
def admin_dashboard_view(request):
    total_users = User.objects.count()
    total_teachers = Profile.objects.filter(role='teacher').count()
    total_students = Profile.objects.filter(role='student').count()
    total_subjects = Subject.objects.count()
    total_groups = ClassGroup.objects.count()
    total_tasks = Task.objects.count()
    total_submissions = Submission.objects.filter(submitted=True).count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    context = {
        'total_users': total_users,
        'total_teachers': total_teachers,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_groups': total_groups,
        'total_tasks': total_tasks,
        'total_submissions': total_submissions,
        'recent_users': recent_users,
    }
    return render(request, 'admin_site/dashboard.html', context)


@superuser_required
def admin_users_view(request):
    role_filter = request.GET.get('role', '')
    users = User.objects.select_related('profile').order_by('username')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    context = {'users': users, 'role_filter': role_filter}
    return render(request, 'admin_site/users.html', context)


@superuser_required
def admin_user_edit_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    profile = target_user.profile
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'student')
        display_name = request.POST.get('display_name', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        if username:
            target_user.username = username
        target_user.email = email
        target_user.is_active = is_active
        target_user.save()
        profile.role = role
        profile.display_name = display_name
        profile.save()
        return redirect('admin_users')
    context = {'target_user': target_user, 'profile': profile}
    return render(request, 'admin_site/user_edit.html', context)


@superuser_required
def admin_subjects_view(request):
    subjects = Subject.objects.select_related('teacher__user').annotate(
        group_count=Count('classgroup')
    )
    teachers = Profile.objects.filter(role='teacher')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        teacher_id = request.POST.get('teacher_id', '')
        if name:
            teacher = get_object_or_404(Profile, id=teacher_id) if teacher_id else None
            Subject.objects.create(name=name, teacher=teacher)
        return redirect('admin_subjects')
    context = {'subjects': subjects, 'teachers': teachers}
    return render(request, 'admin_site/subjects.html', context)


@superuser_required
def admin_subject_edit_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    teachers = Profile.objects.filter(role='teacher')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            subject.delete()
            return redirect('admin_subjects')
        subject.name = request.POST.get('name', subject.name).strip()
        teacher_id = request.POST.get('teacher_id', '')
        subject.teacher = get_object_or_404(Profile, id=teacher_id) if teacher_id else None
        subject.save()
        return redirect('admin_subjects')
    context = {'subject': subject, 'teachers': teachers}
    return render(request, 'admin_site/subject_edit.html', context)


@superuser_required
def admin_groups_view(request):
    groups = ClassGroup.objects.select_related('subject__teacher__user').annotate(
        student_count=Count('groupmembership')
    )
    subjects = Subject.objects.select_related('teacher__user')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        subject_id = request.POST.get('subject_id', '')
        if name and subject_id:
            subject = get_object_or_404(Subject, id=subject_id)
            ClassGroup.objects.create(name=name, subject=subject)
        return redirect('admin_groups')
    context = {'groups': groups, 'subjects': subjects}
    return render(request, 'admin_site/groups.html', context)


@superuser_required
def admin_group_detail_view(request, group_id):
    group = get_object_or_404(ClassGroup, id=group_id)
    memberships = GroupMembership.objects.filter(group=group).select_related('student__user')
    all_students = Profile.objects.filter(role='student').exclude(
        id__in=memberships.values_list('student_id', flat=True)
    )
    subjects = Subject.objects.select_related('teacher__user')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_group':
            group.delete()
            return redirect('admin_groups')
        elif action == 'update_group':
            group.name = request.POST.get('name', group.name).strip()
            subject_id = request.POST.get('subject_id', '')
            if subject_id:
                group.subject = get_object_or_404(Subject, id=subject_id)
            group.save()
        elif action == 'add_student':
            student_id = request.POST.get('student_id')
            if student_id:
                student = get_object_or_404(Profile, id=student_id)
                GroupMembership.objects.get_or_create(student=student, group=group)
        elif action == 'remove_student':
            student_id = request.POST.get('student_id')
            if student_id:
                GroupMembership.objects.filter(student_id=student_id, group=group).delete()
        return redirect('admin_group_detail', group_id=group.id)
    context = {
        'group': group,
        'memberships': memberships,
        'all_students': all_students,
        'subjects': subjects,
    }
    return render(request, 'admin_site/group_detail.html', context)
