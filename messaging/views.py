"""Views чата MVP (Этап 3.7).

Без WebSocket — используем HTMX-поллинг каждые N секунд.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Job
from core.ratelimit import rate_limit

from .models import Conversation, Message


@login_required
def conversation_list(request):
    """Список переписок пользователя."""
    conversations = (
        Conversation.objects
        .filter(participants=request.user)
        .prefetch_related('participants', 'messages')
        .order_by('-updated_at')
    )
    convs_with_meta = []
    for conv in conversations:
        convs_with_meta.append({
            'conv': conv,
            'unread': conv.unread_count_for(request.user),
            'other_names': ', '.join(
                p.get_full_name() or p.username
                for p in conv.participants.all() if p != request.user
            ),
        })
    return render(request, 'messaging/conversation_list.html', {
        'conversations_meta': convs_with_meta,
        'conversations': conversations,
    })


@login_required
@rate_limit(key='start_conversation', limit=20, period=300)
def start_conversation(request, user_id, job_id=None):
    """Начать переписку с пользователем (опц. по вакансии)."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    other = get_object_or_404(User, id=user_id)
    if other == request.user:
        messages.error(request, 'Нельзя начать переписку с самим собой.')
        return redirect('messaging:conversation_list')

    job = None
    if job_id:
        job = get_object_or_404(Job, id=job_id)

    conv, created = Conversation.get_or_create_between(
        request.user, other, job=job,
    )
    return redirect('messaging:conversation_detail', conversation_id=conv.id)


@login_required
def conversation_detail(request, conversation_id):
    """Страница переписки: история + форма отправки + HTMX-поллинг."""
    conv = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id,
    )
    messages_qs = conv.messages.select_related('sender').order_by('created_at')

    Message.objects.filter(
        conversation=conv, read_at__isnull=True,
    ).exclude(sender=request.user).update(read_at=timezone.now())

    other = conv.participants.exclude(id=request.user.id).first()

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conv,
        'messages': messages_qs,
        'other': other,
    })


@login_required
@require_POST
@rate_limit(key='send_message', limit=60, period=60)
def send_message(request, conversation_id):
    """Отправить сообщение (HTMX-эндпоинт, возвращает partial с новым сообщением)."""
    conv = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id,
    )
    body = (request.POST.get('body') or '').strip()
    if not body:
        return HttpResponse(
            '<div class="alert alert-danger">Сообщение не может быть пустым</div>',
            status=400,
        )

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        body=body,
    )
    conv.updated_at = timezone.now()
    conv.save(update_fields=['updated_at'])

    return render(request, 'messaging/partials/message.html', {
        'message': msg,
    })


@login_required
def poll_messages(request, conversation_id):
    """HTMX-эндпоинт для поллинга новых сообщений (каждые N секунд).

    Возвращает partial с сообщениями, у которых id > since (если передан).
    """
    conv = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id,
    )
    since_id = request.GET.get('since', '0')
    try:
        since_id = int(since_id)
    except (TypeError, ValueError):
        since_id = 0

    new_messages = conv.messages.filter(id__gt=since_id).select_related('sender').order_by('created_at')

    Message.objects.filter(
        id__in=[m.id for m in new_messages], read_at__isnull=True,
    ).exclude(sender=request.user).update(read_at=timezone.now())

    return render(request, 'messaging/partials/messages_list.html', {
        'messages': new_messages,
        'since_id': since_id,
    })
