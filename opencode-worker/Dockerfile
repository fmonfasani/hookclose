FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install -U pip wheel \
 && pip install -r requirements.txt

COPY . .

RUN addgroup --system hookclose && adduser --system --ingroup hookclose --home /app hookclose \
 && chown -R hookclose:hookclose /app

USER hookclose

CMD ["python", "main.py"]
