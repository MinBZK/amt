# Python Project Template

## Description

This is a template repository that can be used for Python 3.11 projects and uses the Poetry package manager. By default this project sets up the following:

* Devcontainers for VSCode users
* Github community health files
* Github Dependabot
* VSCode configs
* Some scripts to adhere to programming standards
* A editorconfig file so editors enforce formatting
* A default .gitgignore
* A default pre-commit-config
* A EUPL v1.2 Licence
* A basic Docker setup
* publiccode.yml

## How to use this template repository

When creating a new Repository select this template repository as the base.

After the repository is created make sure to change the following (we may need to consider copier to automate this):

* change the owners in the the .github/CODEOWNERS
* run a global rename command where you rename new_name to your project name
  * macos: `find . -type f -not -path "./.git/*" -exec  sed -i '' "s/python_project/new_name/g" {} \;`
  * linux: `find . -type f -not -path "./.git/*" -exec  sed -i "s/python_project/new_name/g" {} \;`
* rename the python_project/ folder to your project name
* change author and name in pyproject.toml
* change labels in Dockerfile to appropriate values
* Verify the License used
* Change publiccode.yml to your needs
