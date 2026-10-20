from datetime import timedelta

from django.utils import timezone

from orders.models import Order, RefundRequest
from .tracking_data import DELIVERY_DATA


def get_order_details(order_id: int):
    try:
        order = Order.objects.get(id=order_id)
        return {
            "order_id": order.id,
            "product_name": order.product_name,
            "amount": str(order.amount),
            "status": order.status,
            "carrier": order.carrier,
            "tracking_number": order.tracking_number,
            "delivery_address": order.delivery,
            "ordered_on": order.created_at.strftime("%d %b %Y"), # 25 May 2026
            "days_since_order": (timezone.now() - order.created_at).days, # 20
        }
    except Order.DoesNotExist:
        return {
            "error": f"Order with ID {order_id} does not exist"
        }


def get_refund_history(user_id):
    refunds = RefundRequest.objects.filter(user_id=user_id).order_by('-created_at')

    history = []
    for refund in refunds:
        history.append({
            "order_id": refund.order.id,
            "product": refund.order.product_name,
            "reason": refund.reason,
            "status": refund.status,
            "requested_on": refund.created_at.strftime("%d %b %Y"),
        })

    return {
        "total_refund_requests": len(history),
        "refund_history": history,
    }


def check_delivery_status(tracking_number, carrier):
    default_response = {
        "status": "Unknown",
        "last_location": "Tracking info unavailable",
        "last_updated": "N/A",
        "estimated_delivery": "Contact carrier directly",
        "delay_reason": "No updates from carrier",
    }
    delivery_data = DELIVERY_DATA.get(tracking_number, default_response)
    delivery_data["tracking_number"] = tracking_number
    delivery_data["carrier"] = carrier
    return delivery_data


def get_customer_risk_profile(user_id):
    refunds = RefundRequest.objects.filter(user_id=user_id)
    orders = Order.objects.filter(user_id=user_id)

    recent_refund = refunds.filter(created_at__gte=timezone.now() - timedelta(days=90)).count()

    denied = refunds.filter(status="denied").count()
    approved = refunds.filter(status="approved").count()
    pending = refunds.filter(status="pending").count()

    total_orders = orders.count()
    total_refunds = refunds.count()

    if total_orders > 0:
        refund_ratio = round(total_refunds / total_orders, 2) # order = 8, refund 3 = 0.375
    else:
        refund_ratio = 0.0

    return {
        "user_id": user_id,
        "refunds_last_90_days": recent_refund,
        "denied_refunds": denied,
        "approved_refunds": approved,
        "pending_refunds": pending,
        "total_orders": total_orders,
        "total_refunds": total_refunds,
        "refund_ratio": refund_ratio,
    }