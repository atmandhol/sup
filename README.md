# sup
`sup` is an interactive CLI for Tanzu Supply chains.

## Getting Started

### See all latest runs
Make sure your kubeconfig is pointing to the cluster you want to run `sup` against. Run `sup` to launch the home page:

![sup](images/home.png)

- Use the `:` to switch focus to supply chain and status selector for filtering by chain and status.
- The footer bar in the bottom show you all the options on a particular screen.

### Run Details
Hit enter on any one of the runs to see the details page:

![sup](images/details.png)

### Logs for stages
Press `L` to see the logs of any stage:

![sup](images/logs.png)

### Install sup
#### Prerequisites
- Install the latest Python 3.12.x or later from [python.org](https://www.python.org/downloads/)

Recommended way to install tappr is by using [pipx](https://pypa.github.io/pipx/#install-pipx).
You can `brew` install `pipx` as follows:

```bash
brew install pipx
pipx ensurepath
```
To Install latest:
```bash
pipx install git+https://github.com/atmandhol/sup.git
```

If you already have `sup` installed from latest, and want to pull in the new changes:
```bash
pipx reinstall sup
```

- Run `sup` on your command line to confirm if its installed.

![sup](images/home.png)

## Setup for Local

* Install `poetry` on the system level using 
```bash
pip3 install poetry
```
* Create a virtualenv `tappr` using virtualenvwrapper and run install
```bash
mkvirtualenv sup -p python3
poetry install
```

* Run locally
```bash
poetry run sup
```

### Build
Run the following poetry command
```bash
poetry build
```
This will generate a dist folder with a whl file and a tar.gz file.

### Upgrade dependencies
Run the following poetry command
```bash
poetry update
```
