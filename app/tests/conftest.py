import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# 테스트용 SQLite 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 테스트용 데이터베이스 세션 의존성
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 테스트 클라이언트 설정
@pytest.fixture(scope="session")
def test_app():
    # 테스트용 데이터베이스 세션으로 의존성 오버라이드
    app.dependency_overrides[get_db] = override_get_db
    yield app


@pytest.fixture(scope="session")
def client(test_app):
    return TestClient(test_app)


# 각 테스트마다 새로운 데이터베이스 세션을 제공하는 fixture
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
