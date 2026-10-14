from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from .models import Order


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
    context = {
        'order': order,
        'refunds': refunds
    }
    return render(request, 'orders/detail.html', context)