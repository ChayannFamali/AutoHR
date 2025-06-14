FROM python:3.12-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Создаем директории
RUN mkdir -p media staticfiles

# Собираем статику
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Команда для продакшена
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "autohr.wsgi:application"]
