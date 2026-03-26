FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements /workspace/requirements
RUN pip install --no-cache-dir -r /workspace/requirements/base.txt

COPY libs/common /workspace/libs/common
COPY jobs /workspace/jobs
COPY sql /workspace/sql

WORKDIR /workspace
