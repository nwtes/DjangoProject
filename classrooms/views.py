from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import AnnouncementForm
from .models import Announcement, ClassGroup
from pages.decorators import role_required


@login_required
@role_required('teacher')
def create_announcement(request):
    """Allow a teacher to create an announcement for one of their groups."""
    teacher = request.user.profile
    allowed_groups = ClassGroup.objects.filter(subject__teacher=teacher)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        form.fields['group'].queryset = allowed_groups
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = teacher
            announcement.save()
            messages.success(request, "Announcement posted successfully.")
            return redirect('teacher_dashboard')
    else:
        form = AnnouncementForm()
        form.fields['group'].queryset = allowed_groups

    return render(request, "teacher/create_announcement.html", {"form": form})
