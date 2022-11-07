#!/bin/sh

mkdir -p /root/.ssh
cp /client-key.pub /root/.ssh/authorized_keys
chmod go-rwx /root/.ssh/authorized_keys

exec /usr/sbin/sshd -D -e
