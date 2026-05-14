FROM python:3.12-slim-bookworm

LABEL authors="sasha.syrota15@gmail.com"
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

