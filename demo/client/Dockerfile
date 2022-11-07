# Inspiration:
# - https://github.com/eea/eea.docker.rsync/blob/master/Dockerfile
# - https://github.com/eea/eea.docker.rsync/blob/master/docker-entrypoint.sh
# - https://github.com/instrumentisto/rsync-ssh-docker-image/blob/main/Dockerfile

FROM python:3.9-alpine3.16

RUN apk update \
 && apk upgrade \
 && apk add --no-cache \
            rsync openssh-client-default \
            docker-cli-compose \
 && rm -rf /var/cache/apk/*

ENV YOUR_ENV=production
ENV POETRY_VERSION=1.2.2
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY poetry.lock pyproject.toml /app/

RUN mkdir /app/src && touch /app/src/__init__.py && touch /app/README.md \
 && poetry config virtualenvs.create false \
 && poetry install $(test "$YOUR_ENV" == production && echo "--no-dev") --no-interaction --no-ansi

COPY src /app/src
RUN ln -s /app/src/main.py /bin/doco

COPY demo/client/docker-entrypoint.sh /
COPY demo/client/doco.config.toml /

ENTRYPOINT ["/docker-entrypoint.sh"]
