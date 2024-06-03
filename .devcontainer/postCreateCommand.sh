#!/usr/bin/env bash

pipx install poetry
poetry install
poetry run playwright install --with-deps
