import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from src.database import SessionLocal, engine, Base
from src.models import Contact, User
from src.schemas import ContactModel, ResponseContact
from sqlalchemy.orm import Session
from src.main import (
    create_access_token,
    authenticate_user,
    verify_password,
    verify_token,
    send_verification_email,
    send_password_reset_email,
    password_reset_request,
    password_reset
)
from src.repositary.test_contacts import (
    get_contact,
    get_contacts,
    create_contact,
    update_contact,
    remove_contact,
    search_contacts,
    get_upcoming_birthdays
)

class TestYourModule(unittest.TestCase):
    def setUp(self):
        self.engine = engine
        self.Session = SessionLocal
        self.user = User(id=1)
        self.body = ContactModel(
            id=1,
            first_name='John',
            last_name='Doe',
            email='johndoe@gmail.com',
            phone='+38055011222',
            birthday=datetime.date(year=1990, month=1, day=1)
        )

    def test_create_access_token(self):
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        self.assertIsNotNone(token)

    def test_authenticate_user(self):
        # Подготовьте тестовые данные
        db = MagicMock(Session)
        user = MagicMock()
        user.email = "test_user@example.com"
        user.password = "hashed_password"

        # Вызовите функцию с тестовыми данными
        authenticated_user = authenticate_user("test_user@example.com", "password123", db)

        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.email, user.email)

    def test_verify_password(self):
        # Подготовьте тестовые данные
        plain_password = "password123"
        hashed_password = "hashed_password"

        # Вызовите функцию с тестовыми данными
        result = verify_password(plain_password, hashed_password)

        self.assertTrue(result)

    def test_verify_token(self):
        token = create_access_token({"sub": "test_user@example.com"})
        user_email = verify_token(token)

        self.assertEqual(user_email, "test_user@example.com")

    def test_send_verification_email(self):
        # Тестовые данные
        receiver_email = "test_user@example.com"
        verification_code = "123456"

        # Замените следующие строки на реальный код для отправки email, если необходимо
        with self.assertRaises(Exception):  # Замените на более точное исключение
            send_verification_email(receiver_email, verification_code)

    def test_send_password_reset_email(self):
        # Тестовые данные
        receiver_email = "test_user@example.com"
        reset_token = "reset_token123"

        # Замените следующие строки на реальный код для отправки email, если необходимо
        with self.assertRaises(Exception):  # Замените на более точное исключение
            send_password_reset_email(receiver_email, reset_token)

    def test_password_reset_request(self):
        # Тестовые данные
        request = MagicMock()
        request.email = "test_user@example.com"

        # Создайте макет redis_client, например, с использованием unittest.mock
        redis_client = MagicMock()

        # Вызовите функцию с тестовыми данными
        result = password_reset_request(request, db=MagicMock(), redis=redis_client)

        self.assertIsNone(result)

    def test_password_reset(self):
        # Тестовые данные
        reset_token = "reset_token123"
        new_password = "new_password123"

        # Создайте макет redis_client, например, с использованием unittest.mock
        redis_client = MagicMock()

        # Создайте макет db, например, с использованием unittest.mock
        db = MagicMock()

        # Замените следующие строки на реальный код для изменения пароля, если необходимо
        with self.assertRaises(Exception):  # Замените на более точное исключение
            password_reset(reset_token, db, redis_client, new_password)

class TestRepository(unittest.TestCase):
    def setUp(self):
        self.engine = engine
        self.Session = SessionLocal
        self.user = User(id=1)
        self.body = ContactModel(
            id=1,
            first_name='John',
            last_name='Doe',
            email='johndoe@gmail.com',
            phone='+38055011222',
            birthday=datetime.date(year=1990, month=1, day=1)
        )

    def test_create_contact(self):
        db = self.Session()
        expected_contact = Contact()
        self.session.query().filter().first.return_value = expected_contact
        result = create_contact(self.body, self.user, db)
        db.close()
        self.assertEqual(result, expected_contact)

    def test_update_contact(self):
        db = self.Session()
        self.session.query().filter().first.return_value = self.body
        body = ResponseContact(
            id=1,
            first_name="Bob",
            last_name="Willyams",
            email="test@gmail.com",
            phone="+38066911123",
            birthday=datetime.date(year=2000, month=2, day=2)
        )
        result = update_contact(body.id, body, self.user, db)
        db.close()
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)

    def test_get_contact(self):
        db = self.Session()
        expected_contact = Contact()
        db.query().filter().first.return_value = expected_contact
        result = get_contact(1, self.user, db)
        db.close()
        self.assertEqual(result, expected_contact)

    def test_get_contacts(self):
        db = self.Session()
        expected_contacts = [Contact(), Contact()]
        db.query().filter().offset().limit().all.return_value = expected_contacts
        result = get_contacts(0, 3, db, self.user)
        db.close()
        self.assertEqual(result, expected_contacts)

    def test_remove_contact(self):
        db = self.Session()
        expected_contact = Contact()
        db.query().filter().first.return_value = expected_contact
        result = remove_contact(self.user.id, self.user, db)
        db.close()
        self.assertEqual(result, expected_contact)

    def test_search_contacts(self):
        db = self.Session()
        expected_contacts = []
        db.query().filter().all.return_value = expected_contacts
        result = search_contacts("test@test.com", self.user, db)
        db.close()
        self.assertEqual(result, expected_contacts)

    def test_get_upcoming_birthdays(self):
        db = self.Session()
        user = MagicMock()
        user.id = 1
        contact = Contact(birthday=datetime.date.today() + datetime.timedelta(days=1))
        db.query().filter().all.return_value = [contact]
        result = get_upcoming_birthdays(2, user, db)
        db.close()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].birthday, contact.birthday)

if __name__ == '__main__':
    unittest.main()
