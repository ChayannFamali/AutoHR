from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def hr_required(function=None, redirect_field_name=None, login_url=None):
    """Декоратор для проверки, что пользователь - HR специалист"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_hr(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def candidate_required(function=None, redirect_field_name=None, login_url=None):
    """Декоратор для проверки, что пользователь - кандидат"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_candidate(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def admin_required(function=None, redirect_field_name=None, login_url=None):
    """Декоратор для проверки, что пользователь - администратор"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_admin_user(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def role_required(allowed_roles):
    """Декоратор для проверки ролей пользователя"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            
            if request.user.user_type not in allowed_roles and not request.user.is_superuser:
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
