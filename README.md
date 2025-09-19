> [!WARNING]
> **Unreleased version**
>
> You're on the `v3` development branch. This version of pronotepy is not stable.

<br />
<p align="center">
  <a href="https://github.com/bain3/pronotepy">
    <img src="https://pronotepy.readthedocs.io/en/latest/_images/icon.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">pronotepy</h3>

  <p align="center">
    An API wrapper for PRONOTE
    <br />
    <a href="https://pronotepy.readthedocs.io/en/stable"><strong>Explore the docs »</strong></a>
  </p>
</p>

[![pypi version](https://img.shields.io/pypi/v/pronotepy.svg)](https://pypi.org/project/pronotepy/)
[![python version](https://img.shields.io/pypi/pyversions/pronotepy.svg)](https://pypi.org/project/pronotepy/)
[![license](https://img.shields.io/pypi/l/pronotepy.svg)](https://pypi.org/project/pronotepy/)
[![Documentation Status](https://readthedocs.org/projects/pronotepy/badge/?version=latest)](https://pronotepy.readthedocs.io/en/latest/?badge=latest)
[![Run Unit Tests](https://github.com/bain3/pronotepy/actions/workflows/rununittests.yml/badge.svg)](https://github.com/bain3/pronotepy/actions/workflows/rununittests.yml)
[![Mypy Check](https://github.com/bain3/pronotepy/actions/workflows/mypy.yml/badge.svg)](https://github.com/bain3/pronotepy/actions/workflows/mypy.yml)

## Introduction

Pronotepy is a Python API wrapper for the PRONOTE student administration
service. It mainly focuses on student accounts but has limited support for
teacher accounts as well.

## About

### Dependencies

 - pycryptodome
 - aiohttp

### Installation

#### Latest

You can install the latest version by installing directly from the repository:

`pip install -U git+https://github.com/bain3/pronotepy@v3`

We cannot assure that the latest version will be working, but it might have
features or bugfixes that are not yet released on pypi.

### Usage

See the [documentation](https://bain.cz/t/v3docs/).

## Contributing

Feel free to contribute anything. Any help is appreciated. To contribute,
please create a pull request with your changes.

To set up your dev environment, install [`uv`](https://docs.astral.sh/uv/). You
can then `uv sync` to install all the dependencies, including those for
development. To test your changes run `uv run pytest`. For typechecking we use
`uv run mypy src`. You can format your code with `uv run ruff src`.

## Adding content

Pronotepy has most of the essential features covered, but if you need anything
that is not yet implemented, you can [create an
issue](https://github.com/bain3/pronotepy/issues/new) with your request. (or
you can contribute by adding it yourself)

## Funding

This repository is on [issuehunt](https://issuehunt.io/r/bain3/pronotepy). You
can put bounties on your issues if you'd like to thank the person who completes
it. There is no project account for recieving tips, but you're welcome to tip
contributors directly.

## License

This project uses the MIT license. (see LICENSE file)
