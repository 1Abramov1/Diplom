FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директорию для базы данных
RUN mkdir -p /app/data

# Указываем порт
EXPOSE 8000

# Проверка работы
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Запускаем приложение (без --reload для продакшена)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]