# USAGE

This document describes how you can use AMT without building it.

## Using AMT

To use AMT without building we recommend the pre-build docker images
on [github](https://github.com/MinBZK/amt/pkgs/container/amt).

You can deploy AMT to kubernetes or run the container locally using docker compose.

- Example [kubernetes](https://github.com/MinBZK/ai-validation-infra/tree/main/apps/amt)
- Example [docker compose](./compose.yml)

To run amt locally create a compose.yml file and
install [docker desktop](https://www.docker.com/products/docker-desktop/). Once you have install docker you can run the
following command in the directory where you created the compose.yml

```bash
docker compose up
```

Once all services started (can take 1 minute) you can reach the site at localhost:8000

Example of a compose.yml file (this is not a secure example)

```yml
services:
    amt:
        image: ghcr.io/minbzk/amt:main
        restart: unless-stopped
        depends_on:
            db:
                condition: service_healthy
        environment:
            - ENVIRONMENT=local
            - APP_DATABASE_SCHEME=postgresql
            - APP_DATABASE_USER=postgres
            - APP_DATABASE_PASSWORD=changethis
            - APP_DATABASE_DB=postgres
        ports:
            - 8000:8000
        healthcheck:
            test:
                [
                    "CMD-SHELL",
                    "curl -f http://localhost:8000/health/live || exit 1",
                ]
    db:
        image: postgres:16
        restart: unless-stopped
        volumes:
            - app-db-data:/var/lib/postgresql/data/pgdata
        environment:
            - PGDATA=/var/lib/postgresql/data/pgdata
            - POSTGRES_USER=postgres
            - POSTGRES_PASSWORD=changethis
        healthcheck:
            test: ["CMD", "pg_isready", "-q", "-d", "amt", "-U", "amt"]

volumes:
    app-db-data:
```

## Database for AMT

it is possible to run AMT with the following databases:

- SQLite (tested)
- Postgresql (tested)
- MySQL
- MariaDB
- Oracle

We recommend using postgresql for production grade deployments because that one is tested in our CI/CD. By default AMT
will use SQLite which will create a local database within the AMT container.

See [Options](#Option) on how to configure a database

## Logging for AMT

AMT supports detailed logging that gives you control on what to log.

See [Options](#Option) for the logging options.

Currently AMT uses the logging config as defined [here](https://github.com/MinBZK/amt/blob/main/amt/core/log.py). youi
can append or change the config byu setting the LOGGING_CONFIG environmental variable.

```shell
export LOGGING_CONFIG='{"loggers": { "amt": {  "propagate": "True" }},"formatters": { "generic": {  "fmt": "{name}: {message}"}}}'
```

For more info on how to set logging see the
python [logging.config](https://docs.python.org/3/library/logging.config.html) library

## Options

AMT uses environmental options that you can set when running the application.

| Variable                | Description                                                           | Default                     |
| ----------------------- | --------------------------------------------------------------------- | --------------------------- |
| SECRET_KEY              | secret to use                                                         | random                      |
| ENVIRONMENT             | local or production                                                   | local                       |
| LOGGING_LEVEL           | default Logging level "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" | INFO                        |
| LOGGING_CONFIG          | json dict of extra logging config                                     |                             |
| DEBUG                   | enable debugging with trace dumps                                     | False                       |
| AUTO_CREATE_SCHEMA      | Auto create schema, not recommended for production                    | False                       |
| CARD_DIR                | Directory to Card storage                                             | /tmp/                       |
| APP_DATABASE_SCHEME     | one of "sqlite", "postgresql", "mysql", "oracle"                      | sqlite                      |
| APP_DATABASE_DRIVER     | database driver to use                                                | use default based on schema |
| APP_DATABASE_SERVER     | location of the database                                              | db                          |
| APP_DATABASE_PORT       | port of the database                                                  | 5432                        |
| APP_DATABASE_USER       | user of the database                                                  | amt                         |
| APP_DATABASE_PASSWORD   | set a password for the database user                                  |
| APP_DATABASE_DB         | database to connect to on the database server                         | amt                         |
| APP_DATABASE_FILE       | file to use when selecting schema as sqlite                           | /database.sqlite3           |
| CSRF_PROTECT_SECRET_KEY | secret to use                                                         | random                      |
| CSRF_TOKEN_LOCATION     | location of the token                                                 | header                      |
| CSRF_TOKEN_KEY          |                                                                       | csrf-token                  |
| CSRF_COOKIE_SAMESITE    |                                                                       | strict                      |
