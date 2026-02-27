#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

cd /app/wishlists || exit 1

case $1 in
    compose)
        sleep 1
        nohup ./manage.py migrate --noinput --settings=wishlists.settings.compose &
        exec ./manage.py runserver 0.0.0.0:8000 --settings=wishlists.settings.compose ;;
    local)
        nohup ./manage.py collectstatic --noinput --settings=wishlists.settings.local &
        nohup ./manage.py migrate --noinput --settings=wishlists.settings.local &
        exec ./manage.py runserver 0.0.0.0:8000 --settings=wishlists.settings.local ;;
    migrate)
        exec ./manage.py migrate --noinput --settings=wishlists.settings.prod ;;
    *)
        echo "Usage: $0 {compose|local|migrate}"
        exit 1 ;;
esac
