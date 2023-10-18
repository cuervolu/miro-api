# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

FROM python:3.11.0
WORKDIR /app
COPY  . /app
RUN pip install --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt
