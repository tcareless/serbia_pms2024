#!/bin/sh

celery -A pms worker --loglevel=info --concurrency 1 
