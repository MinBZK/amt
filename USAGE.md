# USAGE

This document describes how you can use AMT without building it.

## Using AMT

To use AMT without building we recommend the pre-build docker images
on [github](https://github.com/MinBZK/amt/pkgs/container/amt).

You can deploy AMT to kubernetes or run the container locally using docker compose.

- Example [kubernetes](https://github.com/MinBZK/ai-validation-infra/tree/main/apps/amt)
- Example [docker compose](./compose.yml)

To run amt locally, clone this repository and
install [docker desktop](https://www.docker.com/products/docker-desktop/). Once you have install docker you can run the
following command in the root of the repository:

```bash
docker compose up --build
```

Use `--build` so the image is rebuilt from your checkout; without it, a previously built or pulled image may be reused
that does not match the code (see [BUILD.md](BUILD.md#building-amt-with-containers)). Once all services started (can
take 1 minute) you can reach the site at http://localhost:8070 and log in with `demo` / `demo`. See
[BUILD.md](BUILD.md#local-authentication-with-keycloak) for how the local Keycloak works.

For your own deployment you can create a compose.yml based on the repository
[compose.yml](./compose.yml). AMT authenticates users through OIDC: either include the local Keycloak service from the
repository compose file (it imports the realm from `keycloak/realms/tad.json`, so copy that directory too), or set
`OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` and `OIDC_DISCOVERY_URL` to your own identity provider. It also
needs S3-compatible object storage for measure attachments: include the `minio` and `minio-init` services
from the repository compose file, or point `OBJECT_STORE_*` at your own.

Example of a compose.yml file for a local run (this is not a secure example)

```yml
services:
    amt:
        image: ghcr.io/minbzk/amt:main
        restart: unless-stopped
        depends_on:
            db:
                condition: service_healthy
            keycloak:
                condition: service_healthy
            minio-init:
                condition: service_completed_successfully
        environment:
            - ENVIRONMENT=local
            - APP_DATABASE_SCHEME=postgresql
            - APP_DATABASE_USER=postgres
            - APP_DATABASE_PASSWORD=changethis
            - APP_DATABASE_DB=postgres
            - OIDC_CLIENT_ID=amt-local
            - OIDC_CLIENT_SECRET=devsecret
            - OIDC_DISCOVERY_URL=http://keycloak:8180/realms/tad/.well-known/openid-configuration
            - OBJECT_STORE_URL=minio:9000
            - OBJECT_STORE_USER=amt
            - OBJECT_STORE_PASSWORD=changeme
            - OBJECT_STORE_BUCKET_NAME=amt
        ports:
            - 8070:8000
        healthcheck:
            test:
                [
                    "CMD",
                    "python",
                    "-c",
                    "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health/live').status==200 else 1)",
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
    # Local dev identity provider (demo/demo), see BUILD.md.
    keycloak:
        image: quay.io/keycloak/keycloak:26.7
        restart: unless-stopped
        command:
            [
                "start-dev",
                "--import-realm",
                "--http-port=8180",
                "--hostname=http://localhost:8180",
                "--hostname-backchannel-dynamic=true",
            ]
        environment:
            - KC_BOOTSTRAP_ADMIN_USERNAME=admin
            - KC_BOOTSTRAP_ADMIN_PASSWORD=admin
        volumes:
            - ./keycloak/realms:/opt/keycloak/data/import:ro
        ports:
            - 127.0.0.1:8180:8180
        healthcheck:
            test: ["CMD-SHELL", "bash -c '</dev/tcp/127.0.0.1/8180'"]
            interval: 5s
            timeout: 2s
            retries: 30
            start_period: 20s
    # Local dev object storage for measure attachments, see BUILD.md.
    minio:
        image: minio/minio:RELEASE.2025-09-07T16-13-09Z
        restart: unless-stopped
        command: server /data
        environment:
            - MINIO_ROOT_USER=amt
            - MINIO_ROOT_PASSWORD=changeme
        volumes:
            - app-object-data:/data
        ports:
            - 127.0.0.1:9000:9000
        healthcheck:
            test:
                ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    # One-shot: the bucket must exist before amt starts.
    minio-init:
        image: minio/minio:RELEASE.2025-09-07T16-13-09Z
        restart: "no"
        depends_on:
            minio:
                condition: service_healthy
        entrypoint:
            [
                "sh",
                "-c",
                "mc alias set local http://minio:9000 amt changeme && mc mb --ignore-existing local/amt",
            ]

volumes:
    app-db-data:
    app-object-data:
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

| Variable                 | Description                                                           | Default                     |
| ------------------------ | --------------------------------------------------------------------- | --------------------------- |
| SECRET_KEY               | secret to use                                                         | random                      |
| ENVIRONMENT              | local or production                                                   | local                       |
| LOGGING_LEVEL            | default Logging level "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" | INFO                        |
| LOGGING_CONFIG           | json dict of extra logging config                                     |                             |
| LOG_TO_FILE              | enable logging to file (amt.log)                                      | False                       |
| LOGFILE_LOCATION         | directory path where log file should be written                       | OS temp directory           |
| DEBUG                    | enable debugging with trace dumps                                     | False                       |
| AUTO_CREATE_SCHEMA       | Auto create schema, not recommended for production                    | False                       |
| CARD_DIR                 | Directory to Card storage                                             | /tmp/                       |
| APP_DATABASE_SCHEME      | one of "sqlite", "postgresql", "mysql", "oracle"                      | sqlite                      |
| APP_DATABASE_DRIVER      | database driver to use                                                | use default based on schema |
| APP_DATABASE_SERVER      | location of the database                                              | db                          |
| APP_DATABASE_PORT        | port of the database                                                  | 5432                        |
| APP_DATABASE_USER        | user of the database                                                  | amt                         |
| APP_DATABASE_PASSWORD    | set a password for the database user                                  |
| APP_DATABASE_DB          | database to connect to on the database server                         | amt                         |
| APP_DATABASE_FILE        | file to use when selecting schema as sqlite                           | /database.sqlite3           |
| CSRF_PROTECT_SECRET_KEY  | secret to use                                                         | random                      |
| CSRF_TOKEN_LOCATION      | location of the token                                                 | header                      |
| CSRF_TOKEN_KEY           |                                                                       | csrf-token                  |
| CSRF_COOKIE_SAMESITE     |                                                                       | strict                      |
| OIDC_CLIENT_ID           | OIDC client id                                                        |                             |
| OIDC_CLIENT_SECRET       | OIDC client secret                                                    |                             |
| OIDC_DISCOVERY_URL       | OIDC discovery URL of the identity provider                           | platform Keycloak           |
| OBJECT_STORE_URL         | S3 endpoint for file storage                                          | localhost:9000              |
| OBJECT_STORE_USER        | S3 access key                                                         | amt                         |
| OBJECT_STORE_PASSWORD    | S3 secret key                                                         | changeme                    |
| OBJECT_STORE_BUCKET_NAME | S3 bucket, must exist before AMT starts                               | amt                         |
