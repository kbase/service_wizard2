FROM python:3.11

RUN mkdir -p /app
WORKDIR /app

# install pipenv
RUN pip install --upgrade pip && \
    pip install pipenv

# install deps
COPY Pipfile* /app
RUN pipenv sync --system

COPY ./ /app

# Write the git commit for the service
ARG VCS_REF=no_git_commit_passed_to_build
ENV GIT_COMMIT=$VCS_REF
RUN echo $GIT_COMMIT


ENTRYPOINT ["scripts/entrypoint.sh"]

