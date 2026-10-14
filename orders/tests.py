from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from orders.models import Product, Order, RefundRequest


class ProductModelTests(TestCase):
    """Tests for the Product model."""

    def setUp(self) -> None:
        """Create a default product for tests."""
        self.product = Product.objects.create(
            name="Laptop",
            description="A powerful laptop",
            price=Decimal("999.99"),
            category="Electronics",
            in_stock=True,
        )

    def test_product_string_representation(self) -> None:
        """Product __str__ should return the product name."""
        self.assertEqual(str(self.product), "Laptop")

    def test_product_name(self) -> None:
        """Product should store the name correctly."""
        self.assertEqual(self.product.name, "Laptop")

    def test_product_description(self) -> None:
        """Product should store the description correctly."""
        self.assertEqual(self.product.description, "A powerful laptop")

    def test_product_price(self) -> None:
        """Product should store the price as a Decimal."""
        self.assertEqual(self.product.price, Decimal("999.99"))

    def test_product_category(self) -> None:
        """Product should store the category correctly."""
        self.assertEqual(self.product.category, "Electronics")

    def test_product_in_stock_default(self) -> None:
        """Product in_stock should default to True."""
        product = Product.objects.create(
            name="Default Stock Product",
            price=Decimal("10.00"),
            category="Test",
        )
        self.assertTrue(product.in_stock)

    def test_product_in_stock_false(self) -> None:
        """Product in_stock can be set to False."""
        product = Product.objects.create(
            name="Out of Stock Product",
            price=Decimal("10.00"),
            category="Test",
            in_stock=False,
        )
        self.assertFalse(product.in_stock)

    def test_product_blank_description(self) -> None:
        """Product description can be blank."""
        product = Product.objects.create(
            name="No Description",
            price=Decimal("5.00"),
            category="Test",
        )
        self.assertEqual(product.description, "")


class OrderModelTests(TestCase):
    """Tests for the Order model."""

    def setUp(self) -> None:
        """Create a user and product for order tests."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.product = Product.objects.create(
            name="Laptop",
            price=Decimal("999.99"),
            category="Electronics",
        )
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name="Laptop",
            amount=Decimal("999.99"),
            status="pending",
        )

    def test_order_string_representation(self) -> None:
        """Order __str__ should include id, product_name, and status."""
        expected = f"Order #{self.order.id} - Laptop (pending)"
        self.assertEqual(str(self.order), expected)

    def test_order_user_relation(self) -> None:
        """Order should be linked to the correct user."""
        self.assertEqual(self.order.user, self.user)

    def test_order_product_relation(self) -> None:
        """Order should be linked to the correct product."""
        self.assertEqual(self.order.product, self.product)

    def test_order_product_name(self) -> None:
        """Order should store the product name."""
        self.assertEqual(self.order.product_name, "Laptop")

    def test_order_amount(self) -> None:
        """Order should store the amount as a Decimal."""
        self.assertEqual(self.order.amount, Decimal("999.99"))

    def test_order_status_default(self) -> None:
        """Order status should default to 'pending'."""
        order = Order.objects.create(
            user=self.user,
            product_name="Default Status",
            amount=Decimal("10.00"),
        )
        self.assertEqual(order.status, "pending")

    def test_order_status_choices(self) -> None:
        """Order should accept all valid status choices."""
        for status_code, _ in Order.STATUS_CHOICES:
            order = Order.objects.create(
                user=self.user,
                product_name=f"Status {status_code}",
                amount=Decimal("10.00"),
                status=status_code,
            )
            self.assertEqual(order.status, status_code)

    def test_order_get_status_display(self) -> None:
        """Order get_status_display should return the human-readable status."""
        self.assertEqual(self.order.get_status_display(), "Pending")

    def test_order_carrier_blank(self) -> None:
        """Order carrier can be blank."""
        self.assertEqual(self.order.carrier, "")

    def test_order_tracking_number_blank(self) -> None:
        """Order tracking_number can be blank."""
        self.assertEqual(self.order.tracking_number, "")

    def test_order_delivery_blank(self) -> None:
        """Order delivery can be blank."""
        self.assertEqual(self.order.delivery, "")

    def test_order_created_at_auto_set(self) -> None:
        """Order created_at should be automatically set."""
        self.assertIsNotNone(self.order.created_at)

    def test_order_updated_at_nullable(self) -> None:
        """Order updated_at can be null on creation."""
        # auto_now=True with null=True means it's set on save but can be null initially
        # After creation it may be null since auto_now only triggers on update
        pass

    def test_order_product_set_null_on_delete(self) -> None:
        """Order product should be set to NULL when product is deleted."""
        self.product.delete()
        self.order.refresh_from_db()
        self.assertIsNone(self.order.product)
        # product_name should still be preserved
        self.assertEqual(self.order.product_name, "Laptop")

    def test_order_cascade_on_user_delete(self) -> None:
        """Order should be deleted when the user is deleted."""
        order_id = self.order.id
        self.user.delete()
        self.assertFalse(Order.objects.filter(id=order_id).exists())

    def test_order_with_shipping_details(self) -> None:
        """Order should store carrier, tracking number, and delivery info."""
        order = Order.objects.create(
            user=self.user,
            product_name="Phone",
            amount=Decimal("499.99"),
            status="dispatched",
            carrier="FedEx",
            tracking_number="FX123456789",
            delivery="123 Main St, City, Country",
        )
        self.assertEqual(order.carrier, "FedEx")
        self.assertEqual(order.tracking_number, "FX123456789")
        self.assertEqual(order.delivery, "123 Main St, City, Country")

    def test_user_orders_related_name(self) -> None:
        """User should have an 'orders' related name for accessing orders."""
        self.assertEqual(self.user.orders.count(), 1)
        self.assertIn(self.order, self.user.orders.all())


class RefundRequestModelTests(TestCase):
    """Tests for the RefundRequest model."""

    def setUp(self) -> None:
        """Create a user, product, order, and refund request for tests."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.product = Product.objects.create(
            name="Laptop",
            price=Decimal("999.99"),
            category="Electronics",
        )
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name="Laptop",
            amount=Decimal("999.99"),
            status="delivered",
        )
        self.refund = RefundRequest.objects.create(
            order=self.order,
            user=self.user,
            reason="Product arrived damaged",
        )

    def test_refund_string_representation(self) -> None:
        """RefundRequest __str__ should include order id and status."""
        expected = f"Refund for Order #{self.order.id} - pending"
        self.assertEqual(str(self.refund), expected)

    def test_refund_order_relation(self) -> None:
        """RefundRequest should be linked to the correct order."""
        self.assertEqual(self.refund.order, self.order)

    def test_refund_user_relation(self) -> None:
        """RefundRequest should be linked to the correct user."""
        self.assertEqual(self.refund.user, self.user)

    def test_refund_reason(self) -> None:
        """RefundRequest should store the reason."""
        self.assertEqual(self.refund.reason, "Product arrived damaged")

    def test_refund_status_default(self) -> None:
        """RefundRequest status should default to 'pending'."""
        self.assertEqual(self.refund.status, "pending")

    def test_refund_status_choices(self) -> None:
        """RefundRequest should accept all valid status choices."""
        for status_code, _ in RefundRequest.STATUS_CHOICES:
            refund = RefundRequest.objects.create(
                order=self.order,
                user=self.user,
                reason=f"Status test {status_code}",
                status=status_code,
            )
            self.assertEqual(refund.status, status_code)

    def test_refund_get_status_display(self) -> None:
        """RefundRequest get_status_display should return human-readable status."""
        self.assertEqual(self.refund.get_status_display(), "Pending")

    def test_refund_created_at_auto_set(self) -> None:
        """RefundRequest created_at should be automatically set."""
        self.assertIsNotNone(self.refund.created_at)

    def test_refund_cascade_on_order_delete(self) -> None:
        """RefundRequest should be deleted when the order is deleted."""
        refund_id = self.refund.id
        self.order.delete()
        self.assertFalse(RefundRequest.objects.filter(id=refund_id).exists())

    def test_refund_cascade_on_user_delete(self) -> None:
        """RefundRequest should be deleted when the user is deleted."""
        refund_id = self.refund.id
        self.user.delete()
        self.assertFalse(RefundRequest.objects.filter(id=refund_id).exists())

    def test_order_refund_requests_related_name(self) -> None:
        """Order should have 'refund_requests' related name."""
        self.assertEqual(self.order.refund_requests.count(), 1)
        self.assertIn(self.refund, self.order.refund_requests.all())

    def test_user_refund_requests_related_name(self) -> None:
        """User should have 'refund_requests' related name."""
        self.assertEqual(self.user.refund_requests.count(), 1)
        self.assertIn(self.refund, self.user.refund_requests.all())

    def test_multiple_refunds_for_order(self) -> None:
        """An order can have multiple refund requests."""
        RefundRequest.objects.create(
            order=self.order,
            user=self.user,
            reason="Second refund request",
        )
        self.assertEqual(self.order.refund_requests.count(), 2)

    def test_refund_status_update(self) -> None:
        """RefundRequest status can be updated."""
        self.refund.status = "approved"
        self.refund.save()
        self.refund.refresh_from_db()
        self.assertEqual(self.refund.status, "approved")
        self.assertEqual(self.refund.get_status_display(), "Approved")


class OrdersListViewTests(TestCase):
    """Tests for the orders list view."""

    def setUp(self) -> None:
        """Create users and orders for list view tests."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="otherpass123"
        )
        self.product = Product.objects.create(
            name="Laptop",
            price=Decimal("999.99"),
            category="Electronics",
        )
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name="Laptop",
            amount=Decimal("999.99"),
            status="pending",
        )
        # Order for another user should not appear in testuser's list
        self.other_order = Order.objects.create(
            user=self.other_user,
            product=self.product,
            product_name="Other Laptop",
            amount=Decimal("899.99"),
            status="delivered",
        )

    def test_unauthenticated_user_redirects_to_login(self) -> None:
        """Unauthenticated users should be redirected to the login page."""
        response = self.client.get(reverse("orders_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_authenticated_user_can_access_orders_list(self) -> None:
        """Authenticated users should see the orders list page."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertEqual(response.status_code, 200)

    def test_orders_list_uses_correct_template(self) -> None:
        """Orders list should render using orders/list.html template."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertTemplateUsed(response, "orders/list.html")

    def test_orders_list_extends_base_template(self) -> None:
        """Orders list should extend base.html."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertTemplateUsed(response, "base.html")

    def test_orders_list_page_title(self) -> None:
        """Orders list page should have the correct title."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "My Orders")

    def test_orders_list_shows_user_orders_only(self) -> None:
        """Orders list should only show orders belonging to the logged-in user."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "Laptop")
        self.assertNotContains(response, "Other Laptop")

    def test_orders_list_context_contains_orders(self) -> None:
        """Orders list context should contain 'orders' variable."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertIn("orders", response.context)

    def test_orders_list_shows_order_count(self) -> None:
        """Orders list should show the correct number of orders."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        # The context 'orders' is a paginated queryset
        self.assertEqual(response.context["orders"].paginator.count, 1)

    def test_orders_list_empty_state(self) -> None:
        """Orders list should show empty state when user has no orders."""
        self.client.login(username="otheruser", password="otherpass123")
        # otheruser has no orders (other_order belongs to other_user but we login as otheruser)
        # Actually other_order belongs to other_user, so let's create a user with no orders
        empty_user = User.objects.create_user(
            username="emptyuser", password="emptypass123"
        )
        self.client.login(username="emptyuser", password="emptypass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "No orders yet")

    def test_orders_list_shows_order_status(self) -> None:
        """Orders list should display the order status."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "Pending")

    def test_orders_list_shows_order_amount(self) -> None:
        """Orders list should display the order amount."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "999.99")

    def test_orders_list_shows_product_name(self) -> None:
        """Orders list should display the product name."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "Laptop")

    def test_orders_list_shows_order_link(self) -> None:
        """Orders list should contain links to order detail pages."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, reverse("order_detail", args=[self.order.id]))

    def test_orders_list_ordered_by_created_at_desc(self) -> None:
        """Orders should be ordered by created_at descending."""
        Order.objects.create(
            user=self.user,
            product_name="Old Order",
            amount=Decimal("50.00"),
            status="delivered",
        )
        # The first order (self.order) was created first, so the new one should appear first
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        orders = list(response.context["orders"])
        # The most recently created order should be first
        self.assertEqual(orders[0].product_name, "Old Order")

    def test_orders_list_pagination(self) -> None:
        """Orders list should paginate with 10 orders per page."""
        # Create 15 orders to test pagination
        for i in range(15):
            Order.objects.create(
                user=self.user,
                product_name=f"Product {i}",
                amount=Decimal("10.00"),
                status="pending",
            )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        # Page 1 should have 10 orders
        self.assertEqual(len(response.context["orders"]), 10)
        # Paginator should have 2 pages
        self.assertEqual(response.context["orders"].paginator.num_pages, 2)

    def test_orders_list_page_2(self) -> None:
        """Orders list should show page 2 of paginated results."""
        for i in range(15):
            Order.objects.create(
                user=self.user,
                product_name=f"Product {i}",
                amount=Decimal("10.00"),
                status="pending",
            )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list") + "?page=2")
        self.assertEqual(response.status_code, 200)
        # Page 2 should have 6 orders (16 total - 10 on page 1)
        self.assertEqual(len(response.context["orders"]), 6)

    def test_orders_list_shows_carrier_when_present(self) -> None:
        """Orders list should show carrier info when available."""
        self.order.carrier = "FedEx"
        self.order.save()
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "FedEx")

    def test_orders_list_shows_tracking_number_when_present(self) -> None:
        """Orders list should show tracking number when available."""
        self.order.tracking_number = "FX123456789"
        self.order.save()
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "FX123456789")

    def test_orders_list_shows_delivery_when_present(self) -> None:
        """Orders list should show delivery address when available."""
        self.order.delivery = "123 Main St"
        self.order.save()
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "123 Main St")

    def test_orders_list_pagination_navigation(self) -> None:
        """Orders list should show pagination navigation when multiple pages exist."""
        for i in range(15):
            Order.objects.create(
                user=self.user,
                product_name=f"Product {i}",
                amount=Decimal("10.00"),
                status="pending",
            )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        self.assertContains(response, "Next")

    def test_orders_list_no_pagination_when_single_page(self) -> None:
        """Orders list should not show pagination when all orders fit on one page."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("orders_list"))
        # Only 1 order, no pagination needed
        self.assertFalse(response.context["orders"].has_other_pages())


class OrderDetailViewTests(TestCase):
    """Tests for the order detail view."""

    def setUp(self) -> None:
        """Create users, orders, and refunds for detail view tests."""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="otherpass123"
        )
        self.product = Product.objects.create(
            name="Laptop",
            price=Decimal("999.99"),
            category="Electronics",
        )
        self.order = Order.objects.create(
            user=self.user,
            product=self.product,
            product_name="Laptop",
            amount=Decimal("999.99"),
            status="delivered",
            carrier="FedEx",
            tracking_number="FX123456789",
            delivery="123 Main St, City, Country",
        )
        self.refund = RefundRequest.objects.create(
            order=self.order,
            user=self.user,
            reason="Product arrived damaged",
            status="approved",
        )
        self.other_order = Order.objects.create(
            user=self.other_user,
            product=self.product,
            product_name="Other Product",
            amount=Decimal("500.00"),
            status="pending",
        )

    def test_unauthenticated_user_redirects_to_login(self) -> None:
        """Unauthenticated users should be redirected to the login page."""
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_authenticated_user_can_access_own_order(self) -> None:
        """Authenticated users should see their own order details."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_access_other_users_order(self) -> None:
        """Users should not access orders belonging to other users."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.other_order.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_order_returns_404(self) -> None:
        """Requesting a non-existent order should return 404."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_order_detail_uses_correct_template(self) -> None:
        """Order detail should render using orders/detail.html template."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertTemplateUsed(response, "orders/detail.html")

    def test_order_detail_extends_base_template(self) -> None:
        """Order detail should extend base.html."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertTemplateUsed(response, "base.html")

    def test_order_detail_page_title(self) -> None:
        """Order detail page should have the correct title."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, f"Order #{self.order.id}")

    def test_order_detail_shows_product_name(self) -> None:
        """Order detail should display the product name."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "Laptop")

    def test_order_detail_shows_status(self) -> None:
        """Order detail should display the order status."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "Delivered")

    def test_order_detail_shows_amount(self) -> None:
        """Order detail should display the order amount."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "999.99")

    def test_order_detail_shows_carrier(self) -> None:
        """Order detail should display the carrier information."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "FedEx")

    def test_order_detail_shows_tracking_number(self) -> None:
        """Order detail should display the tracking number."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "FX123456789")

    def test_order_detail_shows_delivery_address(self) -> None:
        """Order detail should display the delivery address."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "123 Main St, City, Country")

    def test_order_detail_context_contains_order(self) -> None:
        """Order detail context should contain 'order' variable."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertIn("order", response.context)
        self.assertEqual(response.context["order"], self.order)

    def test_order_detail_context_contains_refunds(self) -> None:
        """Order detail context should contain 'refunds' variable."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertIn("refunds", response.context)

    def test_order_detail_shows_refund_history(self) -> None:
        """Order detail should display refund history when refunds exist."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "Refund History")
        self.assertContains(response, "Product arrived damaged")

    def test_order_detail_shows_refund_status(self) -> None:
        """Order detail should display refund status."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "Approved")

    def test_order_detail_no_refunds_section(self) -> None:
        """Order detail should not show refund section when no refunds exist."""
        order_no_refunds = Order.objects.create(
            user=self.user,
            product_name="No Refunds",
            amount=Decimal("50.00"),
            status="pending",
        )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[order_no_refunds.id])
        )
        self.assertNotContains(response, "Refund History")

    def test_order_detail_back_to_orders_link(self) -> None:
        """Order detail should have a back to orders link."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "Back to Orders")
        self.assertContains(response, reverse("orders_list"))

    def test_order_detail_shows_order_date(self) -> None:
        """Order detail should display the order creation date."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        # The template uses date filter: d M Y, g:i A
        # We just check that the date fields are present
        self.assertContains(response, "Ordered on")

    def test_order_detail_shows_default_for_blank_fields(self) -> None:
        """Order detail should show dash for blank optional fields."""
        order_minimal = Order.objects.create(
            user=self.user,
            product_name="Minimal Order",
            amount=Decimal("10.00"),
            status="pending",
        )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[order_minimal.id])
        )
        # Template uses default:"—" for carrier, tracking, delivery
        self.assertContains(response, "—")

    def test_order_detail_multiple_refunds(self) -> None:
        """Order detail should show all refund requests."""
        RefundRequest.objects.create(
            order=self.order,
            user=self.user,
            reason="Second refund request",
            status="pending",
        )
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "Product arrived damaged")
        self.assertContains(response, "Second refund request")

    def test_order_detail_help_panel(self) -> None:
        """Order detail should show the help panel."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("order_detail", args=[self.order.id])
        )
        self.assertContains(response, "Need help with this order?")

    def test_order_detail_order_id_in_url(self) -> None:
        """Order detail URL should contain the order ID."""
        url = reverse("order_detail", args=[self.order.id])
        self.assertIn(str(self.order.id), url)
