#!/bin/sh

set -e

python manage.py collectstatic --noinput

# uwsgi --socket :8000 --master --enable-threads --module pms.wsgi 

uwsgi --http 0.0.0.0:80 --master --module pms.wsgi --processes 4 --static-map /media=/app/media_files 
