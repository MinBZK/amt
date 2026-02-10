#!/usr/bin/env bash

DATABASE_MIGRATE=""
HOST="0.0.0.0"
LOGLEVEL="warning"
PORT="8000"

while getopts "dh:l:p:" opt; do
    case $opt in
        d)
            DATABASE_MIGRATE="True"
            ;;
        h)
            HOST=$OPTARG
            ;;
        l)
            LOGLEVEL=$OPTARG
            ;;
        p)
            PORT=$OPTARG
            ;;
        :)
            echo "Option -${OPTARG} requires an argument."
            exit 1
            ;;

        ?)
            echo "Invalid option: $OPTARG"

            echo "Usage: docker-entrypoint.sh [-d] [-h host] [-l loglevel]"
            exit 1
            ;;
    esac
done

echo "DATABASE_MIGRATE: $DATABASE_MIGRATE"
echo "HOST: $HOST"
echo "LOGLEVEL: $LOGLEVEL"
echo "PORT: $PORT"


if [ -z $DATABASE_MIGRATE ]; then
    echo "Upgrading database"
    if ! alembic upgrade head; then
        echo "Failed to upgrade database"
        exit 1
    fi
fi

echo "Starting server"
python -m uvicorn --host "$HOST" amt.server:app --port "$PORT" --log-level "$LOGLEVEL" --proxy-headers
