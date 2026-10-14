"""Reusable test helpers for site-wide tests."""

from django.contrib.auth.models import User
from django.test import Client


# Default test credentials
TEST_USERNAME = 'testuser'
TEST_PASSWORD = 'testpass123'


def create_user(
    username: str = TEST_USERNAME,
    password: str = TEST_PASSWORD,
    email: str | None = None,
    is_active: bool = True,
) -> User:
    """Create a test user with default or custom credentials.

    Args:
        username: The username for the new user.
        password: The password for the new user.
        email: Optional email address.
        is_active: Whether the user account is active.

    Returns:
        The newly created User instance.
    """
    kwargs = {'username': username, 'password': password, 'is_active': is_active}
    if email:
        kwargs['email'] = email
    user = User.objects.create_user(**kwargs)
    return user


def login_form_data(username: str = TEST_USERNAME, password: str = TEST_PASSWORD) -> dict:
    """Return a dictionary of login form data.

    Args:
        username: The username to submit.
        password: The password to submit.

    Returns:
        A dict suitable for passing to client.post().
    """
    return {'username': username, 'password': password}


def post_login(client: Client, username: str = TEST_USERNAME, password: str = TEST_PASSWORD, next_url: str | None = None) -> any:
    """Submit the login form via POST and return the response.

    Args:
        client: The Django test client.
        username: The username to submit.
        password: The password to submit.
        next_url: Optional next parameter for redirect after login.

    Returns:
        The HTTP response from the login view.
    """
    url = '/login/'
    if next_url:
        url = f'/login/?next={next_url}'
    return client.post(url, login_form_data(username, password))
