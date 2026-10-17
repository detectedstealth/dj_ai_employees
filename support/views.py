import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
import time

from orders.models import Order
from support.agents import run_support_agent
from support.models import Conversation, Message


def chat(request, order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message')

        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)

        order = get_object_or_404(Order, id=order_id, user=request.user)

        conversation, created = Conversation.objects.get_or_create(user=request.user, order=order)
        Message.objects.create(conversation=conversation, role='user', content=user_message)

        # Send user message and conversation to LLM

        # store the LLM reply
        llm_reply = run_support_agent(user_message, conversation.id, order.id, request.user.id)
        Message.objects.create(conversation=conversation, role='agent', content=llm_reply)

        return JsonResponse({'reply': llm_reply}, status=200)
    return None
