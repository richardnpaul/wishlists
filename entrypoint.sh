#!/usr/env/bin bash

set -o errexit
set -o nounset
set -o pipefail

cd /app/wishlists || exit 1

case $1 in
    compose)
        nohup python manage.py migrate --noinput --settings=wishlists.settings.compose &
        nohup python manage.py collectstatic --noinput --settings=wishlists.settings.compose &
        exec python manage.py runserver 0.0.0.0:8000 --settings=wishlists.settings.compose ;;
    local)
        nohup python manage.py migrate --noinput --settings=wishlists.settings.local &
        nohup python manage.py collectstatic --noinput --settings=wishlists.settings.local &
        exec python manage.py runserver 0.0.0.0:8000 --settings=wishlists.settings.local ;;
    migrate)
        exec python manage.py migrate --noinput --settings=wishlists.settings.prod ;;
