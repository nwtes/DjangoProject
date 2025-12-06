def global_stats(request):
    data = {
        'user_role': None,
        'subjects_count': 0,
        'ungraded_count': 0,
        'pending_tasks_count': 0,
    }

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return data

    profile = getattr(user, 'profile', None)
    if not profile:
        return data

    data['user_role'] = profile.role

    try:
        if profile.role == 'teacher':
            from classrooms.models import Subject
            from assignments.models import Submission

            data['subjects_count'] = Subject.objects.filter(teacher=profile).count()
            data['ungraded_count'] = Submission.objects.filter(task__created_by=profile, grade__isnull=True).count()

        elif profile.role == 'student':
            from classrooms.models import GroupMembership
            from assignments.models import Task, Submission

            groups = GroupMembership.objects.filter(student=profile).values_list('group', flat=True)
            tasks_in_groups = Task.objects.filter(group__in=groups)
            submitted_task_ids = Submission.objects.filter(student=profile).values_list('task', flat=True)
            data['pending_tasks_count'] = tasks_in_groups.exclude(id__in=submitted_task_ids).count()
    except Exception:
        pass

    return data

