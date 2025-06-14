# core/utils.py
def can_view_sensitive_data(user):
    """Может ли пользователь видеть чувствительные данные (AI оценка, email, телефон)"""
    if not user.is_authenticated:
        return False
    return user.is_hr() or user.is_admin_user()

def can_manage_applications(user):
    """Может ли пользователь управлять заявками (одобрять/отклонять)"""
    if not user.is_authenticated:
        return False
    return user.is_hr() or user.is_admin_user()

def can_export_data(user):
    """Может ли пользователь экспортировать данные"""
    if not user.is_authenticated:
        return False
    return user.is_hr() or user.is_admin_user()
