FROM python:3.10 as base

WORKDIR /app/

# Install Poetry

RUN apt update
RUN apt install -y python3-pip
RUN pip install poetry

RUN poetry config virtualenvs.create false


ENV C_FORCE_ROOT=1


FROM base as dev

COPY ./app/pyproject.toml ./app/poetry.lock* /app/
RUN poetry lock
RUN poetry install --no-root
ENV C_FORCE_ROOT=1

COPY ./app /app
WORKDIR /app

COPY ./app/worker-start-reload.sh /worker-start-reload.sh

RUN chmod +x /worker-start-reload.sh
ENV PYTHONPATH=/app
CMD ["bash", "/worker-start-reload.sh"]


FROM base as prod

COPY ./app/pyproject.toml ./app/poetry.lock* /app/
RUN poetry lock
RUN poetry install --no-root --no-dev

COPY ./app /app
WORKDIR /app

COPY ./app/worker-start.sh /worker-start.sh

RUN chmod +x /worker-start.sh
ENV PYTHONPATH=/app
CMD ["bash", "/worker-start.sh"]