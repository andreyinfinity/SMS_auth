FROM python:alpine

# Задается рабочая дирректорию в контейнере
WORKDIR /code

# Для оптимизации вначале копируются и устанавливаются зависимости
COPY requirements.txt .

RUN pip install -r requirements.txt

# Затем копируется весь проект
COPY . .
