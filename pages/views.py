from django.shortcuts import render, redirect, get_object_or_404
from classrooms.models import ClassGroup,Subject,GroupMembership,Announcement
from assignments.models import Task,Submission

from .forms import TaskCreationForm
from django.db.models import Count
from .decorators import role_required
from accounts.models import Profile
# Create your views here.

def home_view(request):
    return render(request,"home.html")
@role_required('student')
def student_dashboard_view(request):
    student = request.user.profile
    membership = GroupMembership.objects.filter(student = student)
    groups = [m.group for m in membership]
    tasks = Task.objects.filter(group__groupmembership__student=student)
    submission = Submission.objects.filter(student = student)
    return render(request,"dashboard/student.html", {
        "groups" : groups,
        "tasks" : tasks,
        "submission": submission
    })
@role_required('teacher')
def teacher_dashboard_view(request):
    teacher = request.user.profile
    subject = Subject.objects.filter(teacher=teacher)
    groups = ClassGroup.objects.filter(subject__teacher=teacher)
    tasks = Task.objects.filter(created_by = teacher)
    submissions = Submission.objects.filter(task__created_by = teacher,grade__isnull = True)
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
def create_task(request):
    teacher = request.user.profile

    if request.GET.get("subject"):
        subject = request.GET.get("subject")
        allowed_groups = ClassGroup.objects.filter(subject = subject,subject__teacher=teacher)
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

def student_group_view(request,group_id):
    student = request.user.profile
    group = get_object_or_404(ClassGroup, id=group_id)

    students = Profile.objects.filter(
        role='student',
        groups__group=group
    ).distinct()
    context = {
        'group' : group,
        'students': students
    }
    return render(request,'students/student_view_group.html',context)
def teacher_group_view(request):
    teacher = request.user.profile
    group_id = request.GET.get('group_id')
    if group_id:
        current_group = get_object_or_404(ClassGroup,id = group_id)
    else:
        current_group = get_object_or_404(ClassGroup,id = 1)
        if not current_group:
            pass
    groups = ClassGroup.objects.filter(subject__teacher = teacher)
    posts = Announcement.objects.filter(group = current_group)
    students = Profile.objects.filter(
        role='student',
        groups__group = current_group
    ).distinct()
    context = {
        'current_group': current_group,
        'groups' : groups,
        'students': students,
        'announcements' : posts
    }
    return render(request,'teacher/teacher_view_group.html',context)

