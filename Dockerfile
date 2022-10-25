FROM python:3.9-buster

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update && apt-get install nano -y

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY . /code/

RUN chown -R www-data:www-data /code

