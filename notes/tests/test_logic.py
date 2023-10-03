from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

NOTE_TEXT = 'Текст заметки'
NOTE_TITLE = 'Заголовок'
NOTE_SLUG = 'Slug'


class TestNotesCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Йен Сомерхолдер')
        # Адрес страницы с заметкой.
        cls.url = reverse('notes:add')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {'title': NOTE_TITLE, 'text': NOTE_TEXT,
                         'slug': NOTE_SLUG}

    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом заметки.
        self.client.post(self.url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Ожидаем, что заметки в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        self.auth_client.post(self.url, data=self.form_data)
        # Считаем количество заметок.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть одна заметка.
        self.assertEqual(notes_count, 1)
        # Получаем объект заметки из базы.
        notes = Note.objects.get()
        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(notes.title, NOTE_TITLE)
        self.assertEqual(notes.text, NOTE_TEXT)
        self.assertEqual(notes.author, self.author)

    def test_user_cant_use_slug_(self):
        self.auth_client.post(self.url, data=self.form_data)
        # Отправляем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, есть ли в ответе ошибка формы.
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.form_data['slug'] + WARNING
        )
        self.assertEqual(Note.objects.count(), 1)


class TestNotesEditDelete(TestCase):
    # Тексты для заметок не нужно дополнительно создавать
    # (в отличие от объектов в БД), им не нужны ссылки на self или cls,
    # поэтому их можно перечислить просто в атрибутах класса.
    NEW_NOTE_TITLE = 'Новое название заметки'
    NEW_NOTE_TEXT = 'Новый текст заметки'
    NEW_NOTE_SLUG = 'new_note_slug'

    @classmethod
    def setUpTestData(cls):
        # Формируем адрес блока с заметками, который понадобится для тестов
        # Создаём пользователя - автора заметки.
        cls.author = User.objects.create(username='Йен Сомерхолдер')
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём объект заметки.
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            slug=NOTE_SLUG,
            author=cls.author
        )
        # URL для редактирования заметки.
        cls.edit_url = reverse('notes:edit',
                               args=(cls.note.slug,))
        # URL для удаления заметки.
        cls.delete_url = reverse('notes:delete',
                                 args=(cls.note.slug,))
        # Формируем данные для POST-запроса по обновлению заметки.
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG,
        }
        cls.url_success = reverse('notes:success')
        cls.url_add = reverse('notes:add')

    def test_author_can_delete_note(self):
        # От имени автора заметки отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_success)
        # Считаем количество заметок в системе.
        notes_count = Note.objects.count()
        # Ожидаем ноль заметок в системе.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметки по-прежнему на месте.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        # Выполняем запрос на редактирование от имени автора заметки.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.url_success)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст заметки соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, NOTE_TEXT)
