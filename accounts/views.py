from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from .forms import UserRegistrationForm, ProfileForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from assignments.models import Task, Submission
from classrooms.models import ClassGroup, GroupMembership, Subject


def register(request):
    """Handle new user registration and redirect based on role."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            role = form.cleaned_data['role']
            user.profile.role = role
            user.profile.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {"form": form})


class RoleBasedLoginView(LoginView):
    """Custom login view that redirects to the correct dashboard based on user role."""

    def get_success_url(self):
        """Return the URL to redirect to after a successful login."""
        user = self.request.user
        if user.is_superuser:
            return "/admin-site/"
        role = user.profile.role
        if role == "teacher":
            return "/teacher/dashboard"
        elif role == "student":
            return "/student/dashboard"
        return "/"


@login_required
def profile_view(request):
    """Display the current user's profile and role-specific statistics."""
    profile = request.user.profile
    stats = {}
    if profile.role == 'student':
        stats['groups_joined'] = GroupMembership.objects.filter(student=profile).count()
        stats['assignments_completed'] = Submission.objects.filter(student=profile, submitted=True).count()
    elif profile.role == 'teacher':
        stats['subjects_taught'] = Subject.objects.filter(teacher=profile).count()
        stats['total_students'] = GroupMembership.objects.filter(
            group__subject__teacher=profile
        ).values('student').distinct().count()
        stats['tasks_created'] = Task.objects.filter(created_by=profile).count()
    context = {'profile': profile, 'stats': stats}
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """Allow the current user to update their profile details."""
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def user_profile_view(request, user_id):
    """Display another user's public profile page."""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return redirect('profile')
    profile = target_user.profile
    stats = {}
    if profile.role == 'student':
        stats['groups_joined'] = GroupMembership.objects.filter(student=profile).count()
        stats['assignments_completed'] = Submission.objects.filter(student=profile, submitted=True).count()
    elif profile.role == 'teacher':
        stats['subjects_taught'] = Subject.objects.filter(teacher=profile).count()
        stats['tasks_created'] = Task.objects.filter(created_by=profile).count()
    context = {'profile': profile, 'stats': stats, 'target_user': target_user}
    return render(request, 'accounts/user_profile.html', context)
