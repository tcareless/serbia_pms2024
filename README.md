# pms

docker run -d --restart=always -p 80:80 \
    -v /var/run/docker.sock:/tmp/docker.sock:ro \
    jwilder/nginx-proxy

# 1st container
docker run -d --restart=always\
    -e VIRTUAL_HOST=pmdsdata12 \
    -e VIRTUAL_PROTO=uwsgi \
    -e VIRTUAL_PORT=8000 \
    pms:0.1.3  # set to tag on latest version



## Todo:
- remove django-environ: simplify setup
- remove fontawesome: not used currently
- 

## Changelog:
#### 2023-02-12
mysql-connector in alpine:
    https://stackoverflow.com/a/52159090

Deployment examples:
    Initial setup paterned from: https://www.youtube.com/watch?v=nh1ynJGJuT8



