from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db, engine, Base
from app.core.auth import get_current_user
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User
from app.models.todo import Todo
from app.api.auth import router as auth_router
from app.api.todos import router as todo_router

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Todo App", version="1.0.0")

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(todo_router, prefix="/api/v1", tags=["todos"])


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")

    logger.debug(f"Login attempt for email: {email}")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.debug(f"User not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    logger.debug(f"User found: {user.email}")
    logger.debug(
        f"Password verification: {verify_password(password, user.hashed_password)}"
    )

    if not verify_password(password, user.hashed_password):
        logger.debug("Password verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}")
    return response


@app.get("/todos")
async def todos_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todos = db.query(Todo).filter(Todo.user_id == current_user.id).all()
    return templates.TemplateResponse(
        "todos.html", {"request": request, "current_user": current_user, "todos": todos}
    )


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response


@app.post("/create-test-user")
async def create_test_user(db: Session = Depends(get_db)):
    test_password = "testpassword"
    hashed_password = get_password_hash(test_password)
    logger.debug(f"Test password: {test_password}")
    logger.debug(f"Hashed password: {hashed_password}")

    test_user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(test_user)
    db.commit()

    # 생성된 사용자의 해시된 비밀번호를 로깅
    created_user = db.query(User).filter(User.email == "test@example.com").first()
    logger.debug(f"Created user's hashed password: {created_user.hashed_password}")

    return {"message": "Test user created successfully"}
