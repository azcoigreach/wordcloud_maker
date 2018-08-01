FROM python:2.7.15-jessie

WORKDIR /usr/src/app

COPY /app ./

RUN pip install --no-cache-dir --editable .

