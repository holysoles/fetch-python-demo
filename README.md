# About
This Python tool performs availability monitoring of provided URLs. Any HTTP method and arbitrary headers and body can be provided if needed for the endpoint.

Installation and usage directions can be found below, as well as a changelog of descriptions of why each git commit was made to this project.

# Table of Contents
- [About](#about)
- [Table of Contents](#table-of-contents)
- [Installation](#installation)
  - [Linux](#linux)
    - [Via UV (recommended)](#via-uv-recommended)
    - [Via Pip](#via-pip)
  - [Windows](#windows)
    - [Via UV (recommended)](#via-uv-recommended-1)
    - [Via Pip](#via-pip-1)
- [Usage](#usage)
  - [Via UV (if installed via UV)](#via-uv-if-installed-via-uv)
  - [Via Python (if installed via pip)](#via-python-if-installed-via-pip)
- [Changelog](#changelog)


# Installation
This tool has only been tested with Python 3.11 support, but is expected to work with other Python 3 versions. Multiple installation methods are supported:

## Linux

### Via UV (recommended)
- [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- [Install Python via UV](https://docs.astral.sh/uv/guides/install-python/) (if not already installed)

In a new shell:

```bash
git clone https://github.com/holysoles/fetch-python-demo
cd fetch-python-demo
```

### Via Pip
- [Install pip](https://pip.pypa.io/en/stable/installation/)
- [Install Python](https://www.python.org/downloads/) (if not already installed)

In a new shell:

```bash
git clone https://github.com/holysoles/fetch-python-demo.git
cd fetch-python-demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Windows

### Via UV (recommended)

- [Install UV](https://docs.astral.sh/uv/getting-started/installation/)
- [Install Python via UV](https://docs.astral.sh/uv/guides/install-python/) (if not already installed)

In a new PowerShell:

```powershell
git clone https://github.com/holysoles/fetch-python-demo
Set-Location fetch-python-demo
```

### Via Pip

- [Install Python](https://www.python.org/downloads/) (if not already installed)
- [Install pip](https://pip.pypa.io/en/stable/installation/)

In a new PowerShell:

```powershell
git clone https://github.com/holysoles/fetch-python-demo
Set-Location fetch-python-demo
python3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

# Usage

A YAML file must be provided for the tool to consume. An example file can be found in lib/example.yaml

## Via UV (if installed via UV)

```bash
uv run monitor.py <config_file_path>
```

## Via Python (if installed via pip)
```bash
# enter virtualenv if not done already per earlier in installation
python monitor.py <config_file_path>
```

# Changelog
Below is a summary of changes made to this repository, and the justification for each:

- `fix: rename script file per usage documentation`
  - Identified by code review
  - The entrypoint of the script has an error check for its argument count, in which it mentions the script should be called as `monitor.py`
- `fix: add default req method`
  - identified via code review + spec
  - The default request method in the spec is `GET`, but no default request method was previously assumed. A request method must be passed to `requests.request()`
- `fix: ignore URL port when determining domain`
  - identified via code review + spec
  - The spec outlines that the URL should not consider URL ports when calculating the domain that a request should be associated with.
- `feat: only consider endpoint available if res faster than 500ms`
  - identified via code review + spec
  - the spec outlines that URLs should only be considered available if they response in 500ms or less.
- `feat: spin http requests into separate thread`
  - identified via code review + spec
  - the spec outlines that availability should be logged every 15s, regardless of query quantity/total time. Putting the requests in a seperate thread with a mutable argument value lets us acheive this.
- `feat: prep for production`
  - identified from code review
  - this commit adds:
     - a logger (instead of print statements), configurable with environment variables `LOG_LEVEL` and `LOG_FILE`. This allows the user more configuration in how the code might be deployed. The Default log level is `INFO` to preserve all previous output, and `LOG_FILE` can be used to write to a log file in addition to the console output.
     - better error handling so that the user can better understand why the program might not function as expected.
     - type hints for easier future development
 - `chore: format with black, delint with pylint`
   - identified from code review
   - if this code is to be considered production ready, we ensure Python best practices are followed so its easier for developers to contribute to in the future. Two pylint rules were disabled at my discretion since I didn't feel like they were appropriate in this case.
 - `chore: add packaging configuration`
   - chosen to include based on experience
   - Packaging configuration has been setup so that users can install dependencies with `pip`, a classic Python package manager, or `uv`, a newer, much faster package/project manager.
 - `docs: add README and example file`
   - included based on spec
   - provides this document, and an example YAML file for the user to test with for reference
 - `fix: testing fixes`
   - identified via testing a fresh install on Windows (dev done on Linux)
   - fixes
      - mark the monitoring thread as a daemon thread so Python can exit on keyboard interrupt properly 
      - add more logging, particularly an info message that says that monitoring has started
      - pin pyyaml to version that can install on windows (see https://github.com/yaml/pyyaml/issues/601)
      - some cleanup in the install docs