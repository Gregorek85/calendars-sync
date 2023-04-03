docker rm -f calendar_sync
docker build -t calendar_sync --network=host . && docker run -d --name calendar_sync --network=host calendar_sync

