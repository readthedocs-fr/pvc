FROM python:3.10-alpine

WORKDIR /pvc-bot
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT python3 main.py
