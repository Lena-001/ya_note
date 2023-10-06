from http import HTTPStatus

from django.urls import reverse
import pytest
from pytest_django.asserts import assertRedirects


def test_home_availability_for_anonymous_user(client):
    url = reverse('notes:home')
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',  # Имя параметра функции.
    # Значения, которые будут передаваться в name.
    ('notes:home', 'users:login', 'users:logout', 'users:signup')
)
# Указываем имя изменяемого параметра в сигнатуре теста.
def test_pages_availability_for_anonimous_user(client, name):
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'name',
    ('notes:list', 'notes:add', 'notes:success')
)
def test_pages_availability_for_auth_user(admin_client, name):
    url = reverse(name)
    response = admin_client.get(url)
    assert response.status_code == HTTPStatus.OK


# Декоратор на параметризацию по видам клиентов и
#  ожидаемых от них ответов.
@pytest.mark.parametrize(
    # parametriszed_client - название параметра,
    # в который будут передаваться фикстуры.
    # expected_status - ожидаемый статус ответа.
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture(
            'admin_client'
        ), HTTPStatus.NOT_FOUND),  # type: ignore
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)  # type: ignore
    ),
)
# Декоратор на параметризацию по разным страничкам сайта.
@pytest.mark.parametrize(
    'name',
    ('notes:detail', 'notes:edit', 'notes:delete'),
)
def test_page_availability_for_different_users(
    parametrized_client,
    name,
    note,
    expected_status
):
    url = reverse(name, args=(note.slug,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:detail', pytest.lazy_fixture('slug_for_args')),  # type: ignore
        ('notes:edit', pytest.lazy_fixture('slug_for_args')),  # type: ignore
        ('notes:delete', pytest.lazy_fixture('slug_for_args')),  # type: ignore
        ('notes:add', None),
        ('notes:success', None),
        ('notes:list', None),
    ),
)
def test_redirects(client, name, args):
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
