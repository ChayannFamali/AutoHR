FROM python:3.12-slim

# Системные зависимости для psycopg2, Pillow и пр.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости (requirements.txt уже включает psycopg2-binary, redis, celery)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Проект
COPY . .

# Директории для media и собранной статики
RUN mkdir -p media staticfiles

# Собираем статику под prod-настройками
RUN DJANGO_SETTINGS_MODULE=autohr.settings_prod \
    python manage.py collectstatic --noinput

EXPOSE 8000

# По умолчанию gunicorn под prod-настройками.
# В docker-compose можно переопределить command для celery worker / beat.
ENV DJANGO_SETTINGS_MODULE=autohr.settings_prod
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "autohr.wsgi:application"]