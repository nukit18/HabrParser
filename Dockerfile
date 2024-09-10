FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN apt-get -y update
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

