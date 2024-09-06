#!/bin/sh

worker_ready() {
    celery -A pms inspect ping
}

until worker_ready; do
  >&2 echo 'Celery workers not available'
  sleep 1
done
>&2 echo 'Celery workers is available'

celery -A pms  \
    --broker="${CELERY_BROKER_URL}" \
    flower

celery -A pms worker --loglevel=info --concurrency 1 --port=5555