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

## Install older python versions for dev use:

```
# Install deadsnakes ppa if not already installed
sudo apt-get update && sudo apt-get upgrade
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa

# Install versions needed:
sudo apt install python3.9 python3.9-venv 

# set default version back to system python
ls /usr/bin/python*  # list available versions
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.9 2
sudo update-alternatives --config python #set default back to system python

# create venv from python3.9
python3.9 -m venv venv3.9
```

(from https://linux.how2shout.com/install-python-3-9-or-3-8-on-ubuntu-22-04-lts-jammy-jellyfish/#6_Set_the_default_Python_version)



## Todo:
- <s>remove django-environ: simplify setup</s>
- <s>remove fontawesome: not used currently</s>
- add download as CSV to prod-query


## Changelog:

#### <ins>2023-04-25</ins>
Bump Version to 0.1.10
Update barcode scanning to detect failed grade parts and fault out

#### <ins>2023-02-25</ins>
Bump Version to 0.1.7
Added by the week views to prod-query.

#### <ins>2023-02-21</ins>
Zero Downtime Deployment:
- nginx-proxy: https://github.com/nginx-proxy/nginx-proxy
- Check if a container exists: https://yaroslavgrebnov.com/blog/bash-docker-check-container-existence-and-status

Satic file serving with Whitenoise and uWsgi: 
- Whitenoise with Django info: https://whitenoise.evans.io/en/stable/django.html
- uWsgi and Djagno: https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
- Django and wsgi: https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/

#### <ins>2023-02-12</ins>
mysql-connector in alpine:
    https://stackoverflow.com/a/52159090

Deployment examples:
    Initial setup paterned from: https://www.youtube.com/watch?v=nh1ynJGJuT8



## Troubleshooting
Server Access and Cache Errors
When encountering a permission denied error at dnago_cache resulting in a server 500 internal error:

Ensure the correct server IP and port are used. For the development server running the PMS project, use 10.4.1.232:8088 instead of 127.0.0.1:8088.
Modify the launch.json configuration for VS Code to include the correct port and allowed hosts settings:
{
    "name": "PMS on 8088",
    "type": "python",
    "request": "launch",
    "program": "${workspaceFolder}/app/manage.py",
    "args": ["runserver", "0.0.0.0:8088"],
    "env": {
        "ALLOWED_HOSTS": "pmdsdata12,10.4.1.234,10.4.1.232",
        "DEBUG": "1",
    },
    "django": true,
    "justMyCode": false
}
Temporarily disable the cached storage configuration in the settings.py to alleviate the error and allow for successful server operation.