import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationInfo, field_validator


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: str = Field(..., description="ФИО пользователя", min_length=2, max_length=150)  # ✅ вместо username
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

    @field_validator("phone")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """
        Валидатор номера телефона по ТЗ:
        - Должен начинаться с +7
        - Содержать 10 цифр после +7
        """
        if v is None:
            return v

        # Проверка начала с +7
        if not v.startswith("+7"):
            raise ValueError("Телефон должен начинаться с +7")

        # Удаляем все нецифровые символы
        digits = re.sub(r"\D", "", v)

        # Проверяем длину (11 цифр: +7 и 10 цифр)
        if len(digits) != 11:
            raise ValueError("Телефон должен содержать 10 цифр после +7")

        return v


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    password: str = Field(..., description="Пароль")
    password_confirm: str = Field(..., description="Подтверждение пароля")

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """
        Валидация пароля по ТЗ:
        - Не менее 8 символов
        - Только латиница
        - Минимум 1 символ верхнего регистра
        - Минимум 1 спец символ ($%&!:)
        """
        if len(v) < 8:
            raise ValueError("Пароль должен быть не менее 8 символов")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")

        if not re.search(r"[$%&!:]", v):
            raise ValueError("Пароль должен содержать хотя бы один спецсимвол ($%&!:)")

        if not re.match(r"^[A-Za-z0-9$%&!:]+$", v):
            raise ValueError("Пароль должен содержать только латиницу, цифры и спецсимволы $%&!:")

        return v

    @field_validator("password_confirm")
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        """Проверка совпадения паролей."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Пароли не совпадают")
        return v

    @field_validator("email")
    def validate_email(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Проверяет, что если email не указан, то должен быть телефон."""
        if v is None and info.data.get("phone") is None:
            raise ValueError("Необходимо указать email или телефон")
        return v

    @field_validator("phone")
    def validate_phone_field(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Проверяет, что если телефон не указан, то должен быть email."""
        if v is None and info.data.get("email") is None:
            raise ValueError("Необходимо указать email или телефон")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "full_name": "Иван Иванов",
                    "password": "Secret123!",
                    "password_confirm": "Secret123!",
                },
                {
                    "phone": "+79991234567",
                    "full_name": "Петр Петров",
                    "password": "StrongPass1!",
                    "password_confirm": "StrongPass1!",
                },
            ]
        }
    )


class User(UserBase):
    """Схема для отображения пользователя."""

    id: int

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
