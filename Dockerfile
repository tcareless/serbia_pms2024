FROM python:3.9-alpine

ENV PATH="/scripts:${PATH}"

COPY ./requirements.txt /requirements.txt
RUN apk add --no-cache mariadb-connector-c
RUN apk add --update --no-cache --virtual .tmp gcc libc-dev linux-headers mariadb-connector-c-dev
RUN python -m pip install --upgrade pip
RUN pip install -r /requirements.txt
RUN apk del .tmp

RUN mkdir /app
COPY ./app /app
WORKDIR /app
COPY ./scripts /scripts
RUN chmod +x /scripts/*

RUN adduser -D user

EXPOSE 8000

CMD [ "entrypoint.sh" ]
