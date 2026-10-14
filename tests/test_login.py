from django.test import TestCase

from tests.helpers import TEST_PASSWORD, TEST_USERNAME, create_user, post_login


class LoginPageGetTests(TestCase):
    """Tests for accessing the login page via GET request."""

    def test_login_page_status_code(self) -> None:
        """Login page should return HTTP 200."""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_page_uses_correct_template(self) -> None:
        """Login page should render using the login.html template."""
        response = self.client.get('/login/')
        self.assertTemplateUsed(response, 'login.html')

    def test_login_page_extends_base_template(self) -> None:
        """Login page should extend base.html."""
        response = self.client.get('/login/')
        self.assertTemplateUsed(response, 'base.html')

    def test_login_page_title(self) -> None:
        """Login page should have the correct title."""
        response = self.client.get('/login/')
        self.assertContains(response, 'Sign In — Support Center')

    def test_login_page_contains_form(self) -> None:
        """Login page should contain a login form."""
        response = self.client.get('/login/')
        self.assertContains(response, '<form')

    def test_login_page_contains_csrf_token(self) -> None:
        """Login form should contain a CSRF token."""
        response = self.client.get('/login/')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_login_page_contains_username_field(self) -> None:
        """Login form should contain a username input field."""
        response = self.client.get('/login/')
        self.assertContains(response, 'name="username"')

    def test_login_page_contains_password_field(self) -> None:
        """Login form should contain a password input field."""
        response = self.client.get('/login/')
        self.assertContains(response, 'name="password"')

    def test_login_page_contains_submit_button(self) -> None:
        """Login form should contain a Submit button."""
        response = self.client.get('/login/')
        self.assertContains(response, 'Sign In')

    def test_login_page_contains_header(self) -> None:
        """Login page should include the site header."""
        response = self.client.get('/login/')
        self.assertContains(response, 'Support Center')

    def test_login_page_contains_footer(self) -> None:
        """Login page should include the site footer."""
        response = self.client.get('/login/')
        self.assertContains(response, 'All rights reserved')

    def test_login_page_contains_static_css(self) -> None:
        """The login page should link to the static CSS file."""
        response = self.client.get('/login/')
        self.assertContains(response, 'style.css')

    def test_login_page_contains_login_subtitle(self) -> None:
        """Login page should display the support center subtitle."""
        response = self.client.get('/login/')
        self.assertContains(response, 'Access your orders')

    def test_login_page_form_action(self) -> None:
        """Login form should POST to the login URL."""
        response = self.client.get('/login/')
        self.assertContains(response, 'action="/login/"')

    def test_login_page_contains_next_hidden_field(self) -> None:
        """Login form should contain a hidden next field."""
        response = self.client.get('/login/')
        self.assertContains(response, 'name="next"')

    def test_login_page_response_context_has_form(self) -> None:
        """Login page response context should contain a form."""
        response = self.client.get('/login/')
        self.assertIn('form', response.context)


class LoginPagePostTests(TestCase):
    """Tests for submitting the login form via POST request."""

    def setUp(self) -> None:
        """Create a test user for login tests."""
        self.user = create_user()

    def test_login_with_valid_credentials(self) -> None:
        """Valid credentials should log the user in successfully."""
        response = post_login(self.client)
        # Successful login redirects (302)
        self.assertEqual(response.status_code, 302)
        # User should be authenticated
        self.client.login(username=TEST_USERNAME, password=TEST_PASSWORD)
        self.assertTrue(self.client.session['_auth_user_id'])

    def test_login_with_invalid_password(self) -> None:
        """Invalid password should keep the user on the login page."""
        response = post_login(self.client, password='wrongpassword')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')

    def test_login_with_nonexistent_user(self) -> None:
        """Nonexistent user should keep the user on the login page."""
        response = post_login(self.client, username='nonexistent', password='somepassword')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')

    def test_login_with_empty_credentials(self) -> None:
        """Empty credentials should show validation errors."""
        response = post_login(self.client, username='', password='')
        self.assertEqual(response.status_code, 200)
        # Should show field validation errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_login_with_empty_password(self) -> None:
        """Empty password with a valid username should show a validation error."""
        response = post_login(self.client, password='')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_login_redirects_to_admin_by_default(self) -> None:
        """Successful login should redirect to the default LOGIN_REDIRECT_URL."""
        response = post_login(self.client)
        # Django's default redirect is /orders/ that returns 302
        self.assertEqual(response.status_code, 302)
        self.assertIn('/orders/', response.url)

    def test_login_with_next_parameter(self) -> None:
        """Login with the next parameter should redirect to the specified URL."""
        response = post_login(self.client, next_url='/orders/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/orders/')

    def test_login_preserves_next_parameter_in_context(self) -> None:
        """The next parameter should be available in the response context."""
        response = self.client.get('/login/?next=/dashboard/')
        self.assertEqual(response.context.get('next'), '/dashboard/')

    def test_login_form_has_correct_method(self) -> None:
        """Login form should use the POST method."""
        response = self.client.get('/login/')
        self.assertContains(response, 'method="post"')

    def test_login_error_displays_non_field_errors(self) -> None:
        """Login errors should display in the non-field errors section."""
        response = post_login(self.client, password='wrongpassword')
        self.assertTrue(response.context['form'].non_field_errors())


class LoginPageAuthTests(TestCase):
    """Tests for authentication behavior related to the login page."""

    AUTH_USERNAME = 'authuser'
    AUTH_PASSWORD = 'authpass123'

    def setUp(self) -> None:
        """Create a test user."""
        self.user = create_user(
            username=self.AUTH_USERNAME,
            password=self.AUTH_PASSWORD,
            email='auth@example.com',
        )

    def test_authenticated_user_can_access_login_page(self) -> None:
        """Authenticated users can still access the login page."""
        self.client.login(username=self.AUTH_USERNAME, password=self.AUTH_PASSWORD)
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_creates_session(self) -> None:
        """Successful login should create a user session."""
        post_login(self.client, username=self.AUTH_USERNAME, password=self.AUTH_PASSWORD)
        # Re-login to check session
        login_result = self.client.login(username=self.AUTH_USERNAME, password=self.AUTH_PASSWORD)
        self.assertTrue(login_result)
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_login_with_inactive_user(self) -> None:
        """Inactive users should not be able to log in."""
        self.user.is_active = False
        self.user.save()

        response = post_login(self.client, username=self.AUTH_USERNAME, password=self.AUTH_PASSWORD)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())

    def test_login_url_name(self) -> None:
        """Login URL should be named 'login'."""
        from django.urls import reverse
        url = reverse('login')
        self.assertEqual(url, '/login/')

    def test_login_form_autofocus_on_username(self) -> None:
        """Username field should have an autofocus attribute."""
        response = self.client.get('/login/')
        self.assertContains(response, 'autofocus')

    def test_login_form_autocomplete_attributes(self) -> None:
        """Form fields should have autocomplete attributes."""
        response = self.client.get('/login/')
        self.assertContains(response, 'autocomplete="username"')
        self.assertContains(response, 'autocomplete="current-password"')
