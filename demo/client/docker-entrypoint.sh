#!/bin/sh

#ssh-keyscan -p 2222 -t ed25519 localhost 2>/dev/null >> /root/.ssh/known_hosts
echo "$DOCO_SERVER $(cat /host-key.pub)" >> /root/.ssh/known_hosts

#exec rsync -e 'ssh -p 2222' --list-only -- root@localhost:/data

#doco s /client-projects/s1 -aa
#doco backups create /client-projects/s1 --dry-run --verbose
#doco backups create /client-projects/s1
#doco backups raw ls
#doco backups raw ls s1

exec "$@"
