FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /app/

# Install Poetry
ENV INSTALL_DEV=true
RUN apt update
RUN apt install -y python3-pip
RUN pip install poetry

RUN poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./app/pyproject.toml ./app/poetry.lock* /app/
RUN poetry lock
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"
RUN poetry add watchdog
COPY ./app /app
ENV PYTHONPATH=/app

CMD ["/start-reload.sh"]