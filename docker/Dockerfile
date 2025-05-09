# Lightweight Dockerfile for executing code from AI Agent
FROM python:3.11-slim

RUN adduser --disabled-password --home /home/xuser xuser

WORKDIR /home/xuser

USER xuser

CMD ["python", "/home/xuser/code.py"]
