# Inspiration:
# - https://github.com/eea/eea.docker.rsync/blob/master/Dockerfile
# - https://github.com/eea/eea.docker.rsync/blob/master/docker-entrypoint.sh
# - https://github.com/instrumentisto/rsync-ssh-docker-image/blob/main/Dockerfile

FROM alpine:3.16

RUN apk update \
 && apk upgrade \
 && apk add --no-cache \
            rsync openssh \
 && rm -rf /var/cache/apk/*

RUN sed -i "s/^#?PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config

#RUN ssh-keygen -A  # Generate host SSH keys
RUN sed -i "s/^#(HostKey .*ssh_host_ed25519_key)\$/\1/" /etc/ssh/sshd_config

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
