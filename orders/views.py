import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from .models import Order
from support.models import Conversation


@login_required
def orders_list(request):
    orders_qs = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'orders': page_obj
    }
    return render(request, 'orders/list.html', context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # get refund history
    refunds = order.refund_requests.all()

    try:
        conversation = Conversation.objects.get(user=request.user, order=order)
        previous_messages_qs = conversation.messages.order_by('created_at')
        previous_messages = json.dumps([
            {'role': msg.role, 'content': msg.content}
            for msg in previous_messages_qs
        ])
    except Conversation.DoesNotExist:
        conversation = None
        previous_messages = '[]'

    context = {
        'order': order,
        'refunds': refunds,
        'conversation': conversation,
        'previous_messages': previous_messages
    }
    return render(request, 'orders/detail.html', context)