from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database import Base

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_module(module):
    Base.metadata.create_all(bind=engine)

def teardown_module(module):
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_contact():
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "johndoe@example.com",
        "phone_number": "1234567890",
        "birthdate": "2000-01-01",
        "additional_info": "Some additional info"
    }
    response = client.post("/contacts/", json=contact_data)
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"

def test_read_contacts():
    response = client.get("/contacts/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_read_contact():
    response = client.get("/contacts/1")
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"

def test_update_contact():
    update_data = {
        "first_name": "Jane"
    }
    response = client.put("/contacts/1", json=update_data)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Jane"

def test_delete_contact():
    response = client.delete("/contacts/1")
    assert response.status_code == 200