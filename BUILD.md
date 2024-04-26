# Buiding TAD

There are several ways to build and run TAD.

1. poetry
2. container

## Building TAD with Poetry

Poetry is a python package and dependency manager. Before you can install poetry you first need to install python. Please follow [these](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) instructions.

Once you have python available you can install poetry. See [here](https://python-poetry.org/docs/#installation).

Once you have poetry and python install you can start installing the dependencies with the following shell command.

```shell
poetry install
```

when poetry is done installing all dependencies you can start using the tool.

```shell
poetry run python -m tad
```

## Building TAD with Containers

Containers allow use to package software and make it portable and isolated. Before you can run container you first need a container runtime. There are several available but allot of users use [docker desktop](https://www.docker.com/products/docker-desktop/).

Once you install a docker runtime like docker desktop you can start building the applications with this command:

```shell
docker compose build
```

to run the application you use this command:

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

[VSCode](https://code.visualstudio.com/) has great support for devcontainers. If your editor had support for devcontainers you can also use them to start the devcontainer. Devcontaines offer great standardized environments for development.
