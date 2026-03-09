import re
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User as UserModel
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Регистрация нового пользователя по email или телефону.
    """
    try:
        print(f"🔥 Начало регистрации: {user_data}")

        # Проверяем email
        if user_data.email:
            print(f"🔥 Проверка email: {user_data.email}")
            email_exists = await db.execute(select(UserModel).where(UserModel.email == user_data.email))
            if email_exists.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует"
                )

        # Проверяем телефон
        if user_data.phone:
            print(f"🔥 Проверка телефона: {user_data.phone}")
            phone_exists = await db.execute(select(UserModel).where(UserModel.phone == user_data.phone))
            if phone_exists.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким телефоном уже существует"
                )

        # ✅ Проверяем full_name (было username)
        print(f"🔥 Проверка full_name: {user_data.full_name}")
        name_exists = await db.execute(select(UserModel).where(UserModel.full_name == user_data.full_name))
        if name_exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким именем уже существует"
            )

        # Хэшируем пароль
        print("🔥 Хэширование пароля")
        hashed_password = get_password_hash(user_data.password)

        # ✅ Определяем текущее время
        now = datetime.now(timezone.utc)

        # ✅ Создаём пользователя (используем full_name)
        print("🔥 Создание пользователя")
        new_user = UserModel(
            email=user_data.email,
            phone=user_data.phone,
            full_name=user_data.full_name,  # ✅ вместо username
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            created_at=now,
            updated_at=now,
        )

        db.add(new_user)
        print("🔥 Коммит в БД")
        await db.commit()
        print("🔥 Обновление объекта")
        await db.refresh(new_user)

        print(f"🔥 Успех! Пользователь создан: {new_user.id}")
        return new_user

    except HTTPException:
        # Пробрасываем HTTP исключения дальше
        raise
    except Exception as e:
        print(f"🔥🔥🔥 НЕОЖИДАННАЯ ОШИБКА: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> Any:
    """
    Аутентификация пользователя и получение JWT токена.
    - username: может быть email, телефон или full_name
        - password: пароль пользователя
    """
    login_input = form_data.username
    user = None

    # Проверяем, является ли ввод email
    if "@" in login_input:
        result = await db.execute(select(UserModel).where(UserModel.email == login_input))
        user = result.scalar_one_or_none()

    # Проверяем, является ли ввод телефоном
    if not user:
        # Удаляем все нецифровые символы для проверки
        digits = re.sub(r"\D", "", login_input)
        if len(digits) in [10, 11]:
            # Нормализуем телефон
            if len(digits) == 10:
                normalized = f"+7{digits}"
            elif len(digits) == 11 and digits.startswith("8"):
                normalized = f"+7{digits[1:]}"
            elif len(digits) == 11 and digits.startswith("7"):
                normalized = f"+7{digits[1:]}"
            else:
                normalized = f"+7{digits}"

            result = await db.execute(select(UserModel).where(UserModel.phone == normalized))
            user = result.scalar_one_or_none()

    # Если не нашли по email и телефону, ищем по full_name
    if not user:
        result = await db.execute(select(UserModel).where(UserModel.full_name == login_input))
        user = result.scalar_one_or_none()

    # Проверяем наличие пользователя и пароль
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email/телефон/имя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь деактивирован")

    # Создаём токен
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "phone": user.phone, "full_name": user.full_name}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "phone": user.phone, "full_name": user.full_name},
    }
