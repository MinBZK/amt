# Buiding TAD

There are several ways to build and run TAD.

1. Poetry
2. Container

## Building TAD with Poetry

Poetry is a Python package and dependency manager. Before you can install Poetry you first need to install Python. Please follow [these](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) instructions.

Once you have Python available you can install Poetry. See [here](https://python-poetry.org/docs/#installation).

Once you have Poetry and Python installed you can start installing the dependencies with the following shell command.

```shell
poetry install
```

When poetry is done installing all dependencies you can start using the tool.

```shell
poetry run python -m uvicorn tad.main:app
```

## Building TAD with Containers

Containers allows to package software, make it portable, and isolated. Before you can run a container you first need a container runtime. There are several available, but al lot of users use [docker desktop](https://www.docker.com/products/docker-desktop/).

After installing a Docker runtime like Docker Desktop you can start building the applications with this command:

```shell
docker compose build
```

To run the application you use this command:

```shell
docker compose up
```

## Testing, Linting etc

For testing, linting and other feature we use several tools. You can look up the documentation on how to use these:

* [pytest](https://docs.pytest.org/en/)  `poetry run pytest`
* [ruff](https://docs.astral.sh/ruff/) `poetry run ruff format` or `poetry run ruff check --fix`
* [coverage](https://coverage.readthedocs.io/en/) `poetry run coverage report`
* [pyright](https://microsoft.github.io/pyright/#/) `poetry run pyright`

## Devcontainers

[VSCode](https://code.visualstudio.com/) has great support for devcontainers. If your editor has support for devcontainers you can also use them to start the devcontainer. Devcontaines offer great standardized environments for development.

## Updating dependencies

Use poetry to update all python project dependencies
```shell
poetry update
```

Use pre-commit to update all hooks
```shell
pre-commit autoupdate
```
