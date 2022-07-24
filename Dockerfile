FROM python:3.10-alpine

WORKDIR /pvc-bot
COPY . .
RUN pip -r requirements.txt

ENTRYPOINT py main.py
