#!/usr/bin/env bash

. ${NVM_DIR}/nvm.sh && nvm install
npm install

pipx install poetry
poetry install
poetry run playwright install --with-deps
