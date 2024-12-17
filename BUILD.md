# Buiding AMT

Before you can build AMT you first need to clone the git repository:

```
git clone https://github.com/MinBZK/amt.git
cd amt/
```

There are several ways to build and run AMT.

1. Poetry & NPM
2. Container

## Building with Poetry & NPM

AMT uses 2 build systems within its project. One for the frontend (NPM) and one for the backend (Poetry).

Poetry is a Python package and dependency manager. Before you can install Poetry you first need to install Python.
Please follow [these](https://github.com/pyenv/pyenv?amt=readme-ov-file#installation) instructions to install Python
3.12.

Once you have Python available you can install Poetry. See [here](https://python-poetry.org/docs/#installation).

NPM (Node package manager) is a node package and dependency manager. Before you can use NPM we recommend you install
NVM (node version manager). Please
follow[these](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) instructions.

once NVM is install you can execute the following commands to install node and NPM

```bash
nvm install
nvm use
```

Note that the .nvmrc is used to determine the version that is being installed for this project.

Once you have Poetry and NPM installed you can start installing the dependencies with the following shell commands.

```shell
npm install
poetry install
```

When poetry and npm are done installing all dependencies you can start using the tool. you need to start 2 processes

```shell
npm start
```

```shell
poetry run python -m uvicorn amt.server:app --log-level warning
```

## Building AMT with Containers

Containers allows to package software, make it portable, and isolated. Before you can run a container you first need a
container runtime. There are several available, but al lot of users
use [docker desktop](https://www.docker.com/products/docker-desktop/).

After installing a Docker runtime like Docker Desktop you can start building the applications with this command:

```shell
docker compose build
```

To run the application you use this command:

```shell
docker compose up
```

### Suggested development ENVIRONMENT settings

To use a development environment during local development, you can use the following environment options.

```shell
export AUTO_CREATE_SCHEMA=true
```

## Database

We support most SQL database types. You can use the variable `APP_DATABASE_SCHEME` to change the database. The default
scheme is sqlite.

If you change the `models` at amt/models of the application you can generate a new migration file

```shell
alembic revision --autogenerate -m "a message"
```

Please make sure you check the auto generated file in amt/migrations/

to upgrade to the latest version of the database schema use

```shell
alembic upgrade head
```

## Language support

We use babel for translations and a custom yaml for dynamic translations. Babel does not support Frysian, so we added a
custom piece of code to support this. To generate, update or compile the language files, use the script in
./script/translate.

### Known quirks

When running the script/translate update command, Python may give the error

```
ValueError: Unknown extraction method 'jinja2'
```

The solution for this error, is to upgrade/install the setuptools:

```
pip install --upgrade setuptools
```

## Testing, Linting etc

For testing, linting and other feature we use several tools. You can look up the documentation on how to use these:

- [pytest](https://docs.pytest.org/en/) `poetry run pytest`
- [ruff](https://docs.astral.sh/ruff/) `poetry run ruff format` or `poetry run ruff check --fix`
- [coverage](https://coverage.readthedocs.io/en/) `poetry run coverage report`
- [pyright](https://microsoft.github.io/pyright/#/) `poetry run pyright`

## Devcontainers

[VSCode](https://code.visualstudio.com/) has great support for devcontainers. If your editor has support for
devcontainers you can also use them to start the devcontainer. Devcontaines offer great standardized environments for
development.

## Updating dependencies

Use poetry to update all python project dependencies

```shell
poetry update
```

Use pre-commit to update all hooks

```shell
pre-commit autoupdate
```
