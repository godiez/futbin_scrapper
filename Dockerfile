FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1
RUN apk add --no-cache bash
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/