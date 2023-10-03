from django.contrib.auth import get_user_model
from django.test import TestCase
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestHomePage(TestCase):
    URL_ADD = reverse('notes:add')
    URL_LIST = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Тимоти Шаломе')
        cls.reader = User.objects.create(username='Евгений Онегин')
        cls.note = Note.objects.create(title='Заголовок', text='Текст заметки',
                                       slug='slug', author=cls.author)

    def test_news_order(self):
        """Тест сортировки заметок."""
        self.client.force_login(self.author)
        response = self.client.get(self.URL_LIST)
        object_list = response.context['object_list']
        all_pk = [note.pk for note in object_list]
        sorted_pk = sorted(all_pk)
        self.assertEqual(all_pk, sorted_pk)

    def test_authorized_client_has_form(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        response = self.client.get(self.URL_ADD)
        self.assertIn('form', response.context)
