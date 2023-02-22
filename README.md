# pms

## Setup:
1/ Start nginx-proxy with:
```
docker run -d -p 80:80 \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    nginxproxy/nginx-proxy:alpine
```
2/ Checkout the production branch
``` 
git checkout production 
```
3/ change the version variable in the deploy.sh script



## Todo:
- <s>remove django-environ: simplify setup</s>
- <s>remove fontawesome: not used currently</s>
- 

## Changelog:
#### <ins>2023-02-12</ins>
mysql-connector in alpine:
    https://stackoverflow.com/a/52159090

Deployment examples:
    Initial setup paterned from: https://www.youtube.com/watch?v=nh1ynJGJuT8

#### <ins>2023-02-21</ins>
Zero Downtime Deployment:
- nginx-proxy: https://github.com/nginx-proxy/nginx-proxy
- Check if a container exists: https://yaroslavgrebnov.com/blog/bash-docker-check-container-existence-and-status

Satic file serving with Whitenoise and uWsgi: 
- Whitenoise with Django info: https://whitenoise.evans.io/en/stable/django.html
- uWsgi and Djagno: https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
- Django and wsgi: https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/