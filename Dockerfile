FROM python:3.11.4-bookworm

RUN mkdir -p /app
WORKDIR /app

# install pipenv
RUN pip install --upgrade pip && \
    pip install pipenv

# install deps
COPY Pipfile* /app/
RUN pipenv sync --system

# Copy the source code without the .env file or testing files
COPY ./src /app/src
COPY ./scripts /app/scripts

ARG VCS_REF
ARG GIT_COMMIT_HASH
ENV GIT_COMMIT_HASH=${VCS_REF:-${GIT_COMMIT_HASH:-"NO_GIT_COMMIT_PASSED_IN"}}


RUN echo $GIT_COMMIT


ENTRYPOINT ["scripts/entrypoint.sh"]
