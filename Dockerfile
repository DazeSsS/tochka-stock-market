FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env alembic.ini .

EXPOSE 8000
