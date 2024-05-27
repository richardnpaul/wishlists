FROM python:3.14-bookworm AS build_base

RUN mkdir -m 0755 -p /venv /static
RUN python -m venv /venv
RUN useradd --create-home --shell /bin/bash --home-dir /app wishlists
RUN chown -R wishlists:wishlists /venv /static
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

USER wishlists
WORKDIR /app

ENV PATH="/venv/bin:$PATH"

COPY --chown=wishlists:wishlists requirements/ /app/requirements/

RUN pip install --no-cache-dir -r requirements/base.txt


FROM python:3.14-slim-bookworm AS production

RUN useradd --create-home --shell /bin/bash --home-dir /app wishlists
USER wishlists
WORKDIR /app

COPY --chown=wishlists:wishlists --from=build_base /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY --chown=wishlists:wishlists . /app
RUN pip install --no-cache-dir -r /app/requirements/production.txt

CMD ["uwsgi", "--ini", "uwsgi.ini"]


FROM python:3.14-bookworm AS development

RUN wget -qO /usr/bin/uwsgitop https://raw.githubusercontent.com/xrmx/uwsgitop/refs/heads/master/uwsgitop \
    && chmod +x /usr/bin/uwsgitop

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash --home-dir /home/wishlists wishlists
USER wishlists
WORKDIR /app

COPY --chown=wishlists:wishlists --from=build_base /static /static
COPY --chown=wishlists:wishlists --from=build_base /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY --chown=wishlists:wishlists ./requirements/ /app/requirements/

USER wishlists
RUN pip install --no-cache-dir -r /app/requirements/developer.txt

WORKDIR /app/wishlists

CMD ["/app/wishlists/manage.py", "runserver", "0.0.0.0:8000"]
