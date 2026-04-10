FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements /workspace/requirements
RUN pip install --no-cache-dir -r /workspace/requirements/ml_api.txt

COPY libs/common /workspace/libs/common
COPY apps/ml_api /workspace/apps/ml_api

WORKDIR /workspace/apps/ml_api
