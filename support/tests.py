from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import timedelta

from orders.models import Order, Product, RefundRequest
from .models import Conversation, Message, AgentLog
from .tools import get_order_details, get_refund_history, check_delivery_status


class ConversationModelTests(TestCase):
    """Tests for the Conversation model."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.product = Product.objects.create(name='Laptop', price=Decimal('999.99'), category='Electronics')
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name='Laptop',
            amount=Decimal('999.99'),
            status='pending',
        )
        self.conversation = Conversation.objects.create(
            user=self.user,
            order=self.order,
        )

    def test_conversation_creation(self) -> None:
        """Conversation should be created with user and order."""
        self.assertEqual(self.conversation.user, self.user)
        self.assertEqual(self.conversation.order, self.order)
        self.assertIsNotNone(self.conversation.created_at)

    def test_conversation_str(self) -> None:
        """Conversation __str__ should include id, username, and order id."""
        expected = f"Conversation #{self.conversation.id} with testuser for order {self.order.id}"
        self.assertEqual(str(self.conversation), expected)

    def test_conversation_user_relation(self) -> None:
        """User should have access to conversations via related_name."""
        self.assertEqual(self.user.conversations.count(), 1)
        self.assertIn(self.conversation, self.user.conversations.all())

    def test_conversation_order_relation(self) -> None:
        """Order should have access to conversations via related_name."""
        self.assertEqual(self.order.conversations.count(), 1)
        self.assertIn(self.conversation, self.order.conversations.all())

    def test_conversation_cascade_delete_user(self) -> None:
        """Deleting a user should cascade delete their conversations."""
        self.user.delete()
        self.assertEqual(Conversation.objects.count(), 0)

    def test_conversation_cascade_delete_order(self) -> None:
        """Deleting an order should cascade delete its conversations."""
        self.order.delete()
        self.assertEqual(Conversation.objects.count(), 0)

    def test_conversation_created_at_auto_set(self) -> None:
        """created_at should be automatically set on creation."""
        self.assertIsNotNone(self.conversation.created_at)

    def test_multiple_conversations_per_user(self) -> None:
        """A user can have multiple conversations."""
        order2 = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name='Phone',
            amount=Decimal('499.99'),
            status='pending',
        )
        Conversation.objects.create(user=self.user, order=order2)
        self.assertEqual(self.user.conversations.count(), 2)


class MessageModelTests(TestCase):
    """Tests for the Message model."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.product = Product.objects.create(name='Laptop', price=Decimal('999.99'), category='Electronics')
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name='Laptop',
            amount=Decimal('999.99'),
            status='pending',
        )
        self.conversation = Conversation.objects.create(
            user=self.user,
            order=self.order,
        )

    def test_message_creation_user_role(self) -> None:
        """Message should be created with user role."""
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello, I need help with my order.',
        )
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'Hello, I need help with my order.')
        self.assertEqual(message.conversation, self.conversation)

    def test_message_creation_agent_role(self) -> None:
        """Message should be created with agent role."""
        message = Message.objects.create(
            conversation=self.conversation,
            role='agent',
            content='We are checking your request, please wait.',
        )
        self.assertEqual(message.role, 'agent')

    def test_message_str(self) -> None:
        """Message __str__ should include role and content."""
        message = Message.objects.create(
            conversation=self.conversation,
            role='agent',
            content='We are checking your request, please wait.',
        )
        self.assertEqual(str(message), 'agent: We are checking your request, please wait.')

    def test_message_role_choices(self) -> None:
        """Message role should only accept valid choices."""
        valid_roles = ['user', 'agent']
        for role in valid_roles:
            message = Message.objects.create(
                conversation=self.conversation,
                role=role,
                content='Test message',
            )
            self.assertIn(message.role, valid_roles)

    def test_message_conversation_relation(self) -> None:
        """Conversation should have access to messages via related_name."""
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Test message',
        )
        self.assertEqual(self.conversation.messages.count(), 1)

    def test_message_cascade_delete_conversation(self) -> None:
        """Deleting a conversation should cascade delete its messages."""
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Test message',
        )
        self.conversation.delete()
        self.assertEqual(Message.objects.count(), 0)

    def test_message_created_at_auto_set(self) -> None:
        """created_at should be automatically set on creation."""
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Test message',
        )
        self.assertIsNotNone(message.created_at)

    def test_multiple_messages_in_conversation(self) -> None:
        """A conversation can have multiple messages."""
        Message.objects.create(conversation=self.conversation, role='user', content='First message')
        Message.objects.create(conversation=self.conversation, role='agent', content='Second message')
        Message.objects.create(conversation=self.conversation, role='user', content='Third message')
        self.assertEqual(self.conversation.messages.count(), 3)

    def test_message_ordering_by_created_at(self) -> None:
        """Messages should be orderable by created_at."""
        messages = [
            Message.objects.create(conversation=self.conversation, role='user', content=f'Message {i}')
            for i in range(3)
        ]
        ordered = Message.objects.filter(conversation=self.conversation).order_by('created_at')
        self.assertEqual(list(ordered), messages)


class AgentLogModelTests(TestCase):
    """Tests for the AgentLog model."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.product = Product.objects.create(name='Laptop', price=Decimal('999.99'), category='Electronics')
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name='Laptop',
            amount=Decimal('999.99'),
            status='pending',
        )
        self.conversation = Conversation.objects.create(
            user=self.user,
            order=self.order,
        )

    def test_agent_log_creation(self) -> None:
        """AgentLog should be created with conversation, event_type, and message."""
        log = AgentLog.objects.create(
            conversation=self.conversation,
            event_type='support',
            message='Support agent assigned',
        )
        self.assertEqual(log.conversation, self.conversation)
        self.assertEqual(log.event_type, 'support')
        self.assertEqual(log.message, 'Support agent assigned')

    def test_agent_log_event_type_choices(self) -> None:
        """AgentLog event_type should only accept valid choices."""
        valid_types = ['support', 'tool_call', 'tool_result', 'manager', 'risk', 'final']
        for event_type in valid_types:
            log = AgentLog.objects.create(
                conversation=self.conversation,
                event_type=event_type,
                message='Test log',
            )
            self.assertIn(log.event_type, valid_types)

    def test_agent_log_str(self) -> None:
        """AgentLog __str__ should include event_type and truncated message."""
        log = AgentLog.objects.create(
            conversation=self.conversation,
            event_type='tool_call',
            message='This is a very long message that should be truncated in the string representation',
        )
        expected = '[tool_call]: This is a very long message that should '
        self.assertEqual(str(log), expected)

    def test_agent_log_str_short_message(self) -> None:
        """AgentLog __str__ should handle short messages without truncation."""
        log = AgentLog.objects.create(
            conversation=self.conversation,
            event_type='support',
            message='Short',
        )
        expected = '[support]: Short'
        self.assertEqual(str(log), expected)

    def test_agent_log_conversation_relation(self) -> None:
        """Conversation should have access to agent logs via related_name."""
        AgentLog.objects.create(
            conversation=self.conversation,
            event_type='support',
            message='Test log',
        )
        self.assertEqual(self.conversation.agent_logs.count(), 1)

    def test_agent_log_cascade_delete_conversation(self) -> None:
        """Deleting a conversation should cascade delete its agent logs."""
        log = AgentLog.objects.create(
            conversation=self.conversation,
            event_type='support',
            message='Test log',
        )
        self.conversation.delete()
        self.assertEqual(AgentLog.objects.count(), 0)

    def test_agent_log_created_at_auto_set(self) -> None:
        """created_at should be automatically set on creation."""
        log = AgentLog.objects.create(
            conversation=self.conversation,
            event_type='support',
            message='Test log',
        )
        self.assertIsNotNone(log.created_at)

    def test_multiple_agent_logs(self) -> None:
        """A conversation can have multiple agent logs."""
        AgentLog.objects.create(conversation=self.conversation, event_type='support', message='Log 1')
        AgentLog.objects.create(conversation=self.conversation, event_type='tool_call', message='Log 2')
        AgentLog.objects.create(conversation=self.conversation, event_type='final', message='Log 3')
        self.assertEqual(self.conversation.agent_logs.count(), 3)


class GetOrderDetailsTests(TestCase):
    """Tests for the get_order_details tool function."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.product = Product.objects.create(name='Laptop', price=Decimal('999.99'), category='Electronics')
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name='Laptop',
            amount=Decimal('999.99'),
            status='dispatched',
            carrier='DHL',
            tracking_number='BD99281733',
            delivery='123 Main St, Bangalore',
        )

    def test_get_order_details_success(self) -> None:
        """get_order_details should return order information for valid order."""
        result = get_order_details(self.order.id)
        self.assertEqual(result['order_id'], self.order.id)
        self.assertEqual(result['product_name'], 'Laptop')
        self.assertEqual(result['amount'], '999.99')
        self.assertEqual(result['status'], 'dispatched')
        self.assertEqual(result['carrier'], 'DHL')
        self.assertEqual(result['tracking_number'], 'BD99281733')
        self.assertEqual(result['delivery_address'], '123 Main St, Bangalore')

    def test_get_order_details_contains_ordered_on(self) -> None:
        """get_order_details should include formatted ordered_on date."""
        result = get_order_details(self.order.id)
        self.assertIn('ordered_on', result)
        # Format is "DD Mon YYYY"
        self.assertIsNotNone(result['ordered_on'])

    def test_get_order_details_contains_days_since_order(self) -> None:
        """get_order_details should include days_since_order."""
        result = get_order_details(self.order.id)
        self.assertIn('days_since_order', result)
        self.assertIsInstance(result['days_since_order'], int)

    def test_get_order_details_nonexistent_order(self) -> None:
        """get_order_details should return error for nonexistent order."""
        result = get_order_details(99999)
        self.assertIn('error', result)
        self.assertIn('99999', result['error'])

    def test_get_order_details_amount_is_string(self) -> None:
        """get_order_details amount should be returned as string."""
        result = get_order_details(self.order.id)
        self.assertIsInstance(result['amount'], str)


class GetRefundHistoryTests(TestCase):
    """Tests for the get_refund_history tool function."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.product = Product.objects.create(name='Laptop', price=Decimal('999.99'), category='Electronics')
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name='Laptop',
            amount=Decimal('999.99'),
            status='delivered',
        )

    def test_get_refund_history_empty(self) -> None:
        """get_refund_history should return empty history for user with no refunds."""
        result = get_refund_history(self.user.id)
        self.assertEqual(result['total_refund_requests'], 0)
        self.assertEqual(result['refund_history'], [])

    def test_get_refund_history_with_refunds(self) -> None:
        """get_refund_history should return refund history for user with refunds."""
        RefundRequest.objects.create(
            order=self.order,
            user=self.user,
            reason='Product damaged',
            status='approved',
        )
        result = get_refund_history(self.user.id)
        self.assertEqual(result['total_refund_requests'], 1)
        self.assertEqual(len(result['refund_history']), 1)
        self.assertEqual(result['refund_history'][0]['reason'], 'Product damaged')
        self.assertEqual(result['refund_history'][0]['status'], 'approved')
        self.assertEqual(result['refund_history'][0]['order_id'], self.order.id)
        self.assertEqual(result['refund_history'][0]['product'], 'Laptop')

    def test_get_refund_history_multiple_refunds(self) -> None:
        """get_refund_history should return all refunds for a user."""
        order2 = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name='Phone',
            amount=Decimal('499.99'),
            status='delivered',
        )
        RefundRequest.objects.create(order=self.order, user=self.user, reason='Damaged', status='approved')
        RefundRequest.objects.create(order=order2, user=self.user, reason='Wrong item', status='pending')
        result = get_refund_history(self.user.id)
        self.assertEqual(result['total_refund_requests'], 2)

    def test_get_refund_history_ordering(self) -> None:
        """get_refund_history should return refunds ordered by created_at descending."""
        RefundRequest.objects.create(order=self.order, user=self.user, reason='First', status='pending')
        RefundRequest.objects.create(order=self.order, user=self.user, reason='Second', status='approved')
        result = get_refund_history(self.user.id)
        self.assertEqual(result['refund_history'][0]['reason'], 'Second')
        self.assertEqual(result['refund_history'][1]['reason'], 'First')

    def test_get_refund_history_other_user(self) -> None:
        """get_refund_history should not return refunds for other users."""
        other_user = User.objects.create_user(username='otheruser', password='testpass123')
        RefundRequest.objects.create(order=self.order, user=self.user, reason='Damaged', status='pending')
        result = get_refund_history(other_user.id)
        self.assertEqual(result['total_refund_requests'], 0)

    def test_get_refund_history_contains_requested_on(self) -> None:
        """get_refund_history entries should contain formatted requested_on date."""
        RefundRequest.objects.create(order=self.order, user=self.user, reason='Damaged', status='pending')
        result = get_refund_history(self.user.id)
        self.assertIn('requested_on', result['refund_history'][0])


class CheckDeliveryStatusTests(TestCase):
    """Tests for the check_delivery_status tool function."""

    def test_check_delivery_status_known_tracking(self) -> None:
        """check_delivery_status should return tracking data for known tracking numbers."""
        result = check_delivery_status('BD99281733', 'DHL')
        self.assertEqual(result['status'], 'In Transit')
        self.assertEqual(result['last_location'], 'Bangalore Sorting Hub')
        self.assertEqual(result['tracking_number'], 'BD99281733')
        self.assertEqual(result['carrier'], 'DHL')

    def test_check_delivery_status_delivered(self) -> None:
        """check_delivery_status should return delivered status for delivered packages."""
        result = check_delivery_status('DL44729103', 'DHL')
        self.assertEqual(result['status'], 'Delivered')
        self.assertEqual(result['last_location'], 'Delivered to door')

    def test_check_delivery_status_unknown_tracking(self) -> None:
        """check_delivery_status should return default response for unknown tracking numbers."""
        result = check_delivery_status('UNKNOWN123', 'DHL')
        self.assertEqual(result['status'], 'Unknown')
        self.assertEqual(result['last_location'], 'Tracking info unavailable')
        self.assertEqual(result['tracking_number'], 'UNKNOWN123')
        self.assertEqual(result['carrier'], 'DHL')

    def test_check_delivery_status_contains_all_fields(self) -> None:
        """check_delivery_status should return all expected fields."""
        result = check_delivery_status('BD99281733', 'DHL')
        expected_fields = ['status', 'last_location', 'last_updated', 'estimated_delivery', 'delay_reason', 'tracking_number', 'carrier']
        for field in expected_fields:
            self.assertIn(field, result)

    def test_check_delivery_status_customs_delay(self) -> None:
        """check_delivery_status should return customs delay reason when applicable."""
        result = check_delivery_status('EK556612309', 'FedEx')
        self.assertEqual(result['delay_reason'], 'Customs clearance delay')

    def test_check_delivery_status_no_delay(self) -> None:
        """check_delivery_status should return None for delay_reason when no delay."""
        result = check_delivery_status('BD10293847', 'DHL')
        self.assertIsNone(result['delay_reason'])

    def test_check_delivery_status_all_known_trackings(self) -> None:
        """check_delivery_status should work for all known tracking numbers."""
        known_trackings = ['BD99281733', 'DL44729103', 'EK556612309', 'BD10293847']
        for tracking in known_trackings:
            result = check_delivery_status(tracking, 'DHL')
            self.assertNotEqual(result['status'], 'Unknown')
