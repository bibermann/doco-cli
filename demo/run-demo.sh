#!/usr/bin/env bash
set -euo pipefail

if [ ! -d keys ]; then
  mkdir -p keys/etc/ssh
  ssh-keygen -A -f keys  # Generate host SSH keys
  ssh-keygen -t ed25519 -N "" -f keys/id_ed25519  # Generate public/private key pair
fi

export DOCKER_BUILDKIT=1  # Necessary to support demo/client/Dockerfile.dockerignore

DOCO_NETWORK=doco-demo
DOCO_SERVER=doco-demo-server
DOCO_CLIENT=doco-demo-client

COLOR_OFF='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_BOLD_GREEN='\033[1;32m'

docker network create $DOCO_NETWORK || true

docker build \
  -t $DOCO_SERVER \
  server

docker build \
  -t $DOCO_CLIENT \
  .. -f client/Dockerfile


finish() {
  set -x
  docker stop $DOCO_SERVER || true
}
trap finish EXIT

SERVER_DOCKER_ARGS=(
  -v "$PWD/keys/etc/ssh/ssh_host_ed25519_key":/etc/ssh/ssh_host_ed25519_key:ro
  -v "$PWD/keys/etc/ssh/ssh_host_ed25519_key.pub":/etc/ssh/ssh_host_ed25519_key.pub:ro
  -v "$PWD/keys/id_ed25519.pub:/client-key.pub":ro
  --network "$DOCO_NETWORK"
)

CLIENT_DOCKER_ARGS=(
  -v "$PWD/keys/id_ed25519":/root/.ssh/id_ed25519
  -v "$PWD/keys/id_ed25519.pub":/root/.ssh/id_ed25519.pub
  -v "$PWD/keys/etc/ssh/ssh_host_ed25519_key.pub":/host-key.pub:ro
  -e "DOCO_SERVER=$DOCO_SERVER"
  --network "$DOCO_NETWORK"
)

docker run --rm -d --name $DOCO_SERVER \
  "${SERVER_DOCKER_ARGS[@]}" \
  $DOCO_SERVER

# Try connecting to $DOCO_SERVER 3 times
RETRY_COUNTER=1
MAX_RETRIES=3
while [ $RETRY_COUNTER -le $MAX_RETRIES ]
do
  if docker run --rm "${CLIENT_DOCKER_ARGS[@]}" $DOCO_CLIENT ssh -T $DOCO_SERVER; then
    break
  else
    if [ $RETRY_COUNTER -eq $MAX_RETRIES ]; then echo >&2 Server did not respond.; exit 1; fi
    sleep 1
    RETRY_COUNTER=$(( RETRY_COUNTER + 1 ))
  fi
done

doco() {
  echo -en "$COLOR_GREEN"
  echo "=============================="
  echo -en "${COLOR_BOLD_GREEN}doco${COLOR_GREEN} "
  echo "$*"
  echo "=============================="
  echo -en "$COLOR_OFF"
  docker run --rm -t -e TERM \
    "${CLIENT_DOCKER_ARGS[@]}" \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v "$PWD/client-projects":/client-projects \
    $DOCO_CLIENT \
    doco "$@"
}

truncate -s 0 client-projects/s1/.last-backup-dir
mkdir -p client-projects/s1-volume-rw
rm -f client-projects/s1-volume-rw/*

echo "Test S1 static" >client-projects/s1-volume-rw/test-static.txt
echo "Test S1 rw" >client-projects/s1-volume-rw/test.txt

doco s /client-projects/s1 -aa
doco backups create /client-projects/s1 -b backup1 --dry-run --verbose
doco backups create /client-projects/s1 -b backup1

echo "Test S1 rw changed" >client-projects/s1-volume-rw/test.txt

doco backups create /client-projects/s1 -b backup2

doco backups raw ls
doco backups raw ls s1

rm -rf server-backups
docker cp $DOCO_SERVER:/backups server-backups
echo -en "$COLOR_GREEN"
echo "=============================="
echo -e "${COLOR_BOLD_GREEN}tree${COLOR_GREEN} --inodes server-backups"
echo "=============================="
echo -en "$COLOR_OFF"
tree --inodes server-backups

echo -en "$COLOR_GREEN"
echo "In the output of 'tree' above, you should see that the inodes of the unchanged files"
echo "server-backups/s1/backup{1,2}/volumes/doco-test-s1/volume-rw/test-static.txt"
echo "are identical."
echo -en "$COLOR_OFF"
