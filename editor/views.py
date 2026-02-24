from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max, OuterRef, Subquery
from .models import DirectMessage

def pyodide_editor(request):
    return render(request, 'tasks/pyodide_editor.html')


@login_required
def dm_inbox(request):
    me = request.user
    partners_ids = DirectMessage.objects.filter(
        Q(sender=me) | Q(recipient=me)
    ).values_list('sender_id', 'recipient_id')

    seen = set()
    for s, r in partners_ids:
        pid = r if s == me.id else s
        seen.add(pid)
    seen.discard(me.id)

    conversations = []
    for uid in seen:
        partner = User.objects.select_related('profile').get(id=uid)
        last_msg = DirectMessage.objects.filter(
            Q(sender=me, recipient=partner) | Q(sender=partner, recipient=me)
        ).order_by('-sent_at').first()
        unread = DirectMessage.objects.filter(sender=partner, recipient=me, read=False).count()
        conversations.append({
            'partner': partner,
            'last_msg': last_msg,
            'unread': unread,
        })

    conversations.sort(key=lambda c: c['last_msg'].sent_at if c['last_msg'] else 0, reverse=True)

    context = {'conversations': conversations}
    return render(request, 'dm/inbox.html', context)


@login_required
def dm_conversation(request, user_id):
    me = request.user
    other = get_object_or_404(User, id=user_id)
    messages = DirectMessage.objects.filter(
        Q(sender=me, recipient=other) | Q(sender=other, recipient=me)
    ).order_by('sent_at')
    DirectMessage.objects.filter(sender=other, recipient=me, read=False).update(read=True)
    context = {
        'other': other,
        'messages': messages,
    }
    return render(request, 'dm/conversation.html', context)
