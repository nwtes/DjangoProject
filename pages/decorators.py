from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(allowed_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if hasattr(request.user, 'profile') and request.user.profile.role == allowed_role:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator


def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped
