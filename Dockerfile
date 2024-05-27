FROM python:3.8-bullseye as build_base

RUN python -m venv /venv
RUN useradd --create-home --shell /bin/bash --home-dir /app wishlists
RUN chown -R wishlists:wishlists /venv

USER wishlists
WORKDIR /app

ENV PATH="/venv/bin:$PATH"

COPY --chown=wishlists:wishlists requirements/ /app/requirements/

RUN pip install --no-cache-dir -r requirements/base.txt


FROM python:3.8-slim-bullseye as production

RUN useradd --create-home --shell /bin/bash --home-dir /app wishlists
USER wishlists
WORKDIR /app

COPY --chown=wishlists:wishlists --from=build_base /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY --chown=wishlists:wishlists . /app
RUN pip install --no-cache-dir -r /app/requirements/production.txt

CMD ["uwsgi", "--ini", "uwsgi.ini"]


FROM python:3.8-bullseye as development

RUN useradd --create-home --shell /bin/bash --home-dir /home/wishlists wishlists
USER wishlists
WORKDIR /app

COPY --chown=wishlists:wishlists --from=build_base /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY --chown=wishlists:wishlists ./requirements/ /app/requirements/

USER wishlists
RUN pip install --no-cache-dir -r /app/requirements/developer.txt

WORKDIR /app/wishlists

CMD ["/app/wishlists/manage.py", "runserver", "0.0.0.0:8000"]
