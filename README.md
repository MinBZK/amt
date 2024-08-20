# Algorithm Management Toolkit (AMT)

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/minbzk/amt/ci.yml?label=tests)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=MinBZK_amt&metric=coverage)](https://sonarcloud.io/summary/new_code?id=MinBZK_amt)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=MinBZK_amt&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=MinBZK_amt)
![GitHub Release](https://img.shields.io/github/v/release/minbzk/amt?include_prereleases&sort=semver)
![GitHub License](https://img.shields.io/github/license/minbzk/amt)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=MinBZK_amt&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=MinBZK_amt)

AMT is a modern tool to apply technical and non-technical tests for an AI model.

Note: The main branch may be in an unstable or even broken state during development. Please use releases instead of the main branch.

## How to contribute

See [contributing docs](CONTRIBUTING.md)

## How to build and run AMT

See [build docs](BUILD.md)

## How to run the CLI

The check-state can be executed to see what tasks are waiting to be done.

It requires 2 parameters. The first parameter is a list of instrument urns joined by a comma without
spaces. The second parameter is the location of the system card.

An example command:

```shell
./check-state urn:nl:aivt:ir:td:1.0 urn:nl:aivt:ir:iama:1.0 example/system_test_card.yaml
```

### For developers

When running the GitHub actions locally you can use [act](https://github.com/nektos/act), to do this run change the
matrix in the `ci.yml` of the `test-local` job to have only python version 3.11. Then run the following command:
```shell
act -W '.github/workflows/ci.yml' -s GITHUB_TOKEN="$(gh auth token)" --artifact-server-path tmp/artifacts -e act_event.json
```
