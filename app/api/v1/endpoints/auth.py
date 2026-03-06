from app.core.security import verify_password, create_access_token, get_password_hash
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, User as UserSchema
from typing import Any

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя

    - **email**: должен быть уникальным
    - **username**: должен быть уникальным
    - **password**: будет захэширован
    """
    # Проверяем, существует ли пользователь с таким email
    result = await db.execute(
        select(UserModel).where(UserModel.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )

    # Проверяем, существует ли пользователь с таким username
    result = await db.execute(
        select(UserModel).where(UserModel.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует"
        )

    # Хэшируем пароль
    from app.core.security import get_password_hash
    try:
        hashed_password = get_password_hash(user_data.password)
    except ValueError as e:
        if "password cannot be longer than 72 bytes" in str(e):
            # Обрезаем пароль до 72 байт (для bcrypt на Windows)
            password_bytes = user_data.password.encode('utf-8')[:72]
            hashed_password = get_password_hash(password_bytes.decode('utf-8', errors='ignore'))
        else:
            raise

    # Создаём нового пользователя
    new_user = UserModel(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login")
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Аутентификация пользователя и получение JWT токена

    - **username**: может быть email или username
    - **password**: пароль пользователя

    Возвращает access token для авторизации в защищённых эндпоинтах
    """
    # Ищем пользователя по email или username
    result = await db.execute(
        select(UserModel).where(
            (UserModel.email == form_data.username) |
            (UserModel.username == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email/username или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем пароль
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email/username или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь деактивирован"
        )

    # Создаём JWT токен
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username
        }
    }