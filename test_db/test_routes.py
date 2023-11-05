import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from main import app  # Замініть `your_app` на назву вашого додатку
from models import YourModel  # Замініть `YourModel` на модель, яку ви тестуєте

@pytest.fixture
def test_db():
    DATABASE_URL = "postgresql://test_user:test_password@localhost/test_database"  # Замініть на ваші дані для тестової бази
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(engine)

def test_your_route(test_db):
    # Створіть об'єкти моделей та додайте їх до тестової бази даних
    model1 = YourModel(name="Item 1")
    model2 = YourModel(name="Item 2")
    test_db.add(model1)
    test_db.add(model2)
    test_db.commit()

    # Викличте ваш маршрут і отримайте відповідь
    client = app.test_client()
    response = client.get('/your_route')  # Замініть '/your_route' на шлях до вашого маршруту

    # Перевірте, чи відповідь містить очікувані дані
    assert b"Item 1" in response.data
    assert b"Item 2" in response.data

# Запустіть тести за допомогою pytest:
# В командному рядку виконайте команду:
# pytest test_routes.py
