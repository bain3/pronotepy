> [!WARNING]
>**Maintenance mode**
>
> Pronotepy is currently in maintenance mode. **We will continue to fix bugs** and adapt to PRONOTE changes, but will not be adding
> new features. **Please do NOT create PRs with new features.** They will not get merged.
>
> If you are looking for an alternative that is under active developement, consider using [Pawnote](https://github.com/LiterateInk/Pawnote) (JavaScript/TS) instead.

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

Pronotepy is a Python API wrapper for the PRONOTE student administration service. It mainly focuses on student accounts but has limited support for teacher accounts as well.
This project does **not** use the official HYPERPLANNING API provided by PRONOTE, which is inaccessible to students.

## About

### Dependencies

 - pycryptodome
 - beautifulsoup4
 - requests
 - autoslot

### Installation
#### Stable

Install directly from pypi using pip: `pip install -U pronotepy`

> [!NOTE]
If you are on Windows and have trouble with this command, use `py -3 -m pip install pronotepy`. You must have Python 3 installed on your machine.

#### Latest

You can install the latest version by installing directly from the repository:

`pip install -U git+https://github.com/bain3/pronotepy`

We cannot assure that the latest version will be working, but it might have features or bugfixes that are not yet released on pypi.

### Testing the package
To self test pronotepy run this command:

`python -m pronotepy.test_pronotepy`

*Please keep in mind that this uses the demo version of pronote and so it can't test every function.*

### Usage

> [!WARNING]
The usage part of this readme is for the latest version. If you are installing from pypi, please see the documentation linked at the beginning.

Here is an example script (homework shown in example.py):
```python
import pronotepy

import datetime
from pathlib import Path
import json

# load login from `python3 -m pronotepy.create_login` command.
# See quickstart in documentation for other login methods.
credentials = json.loads(Path("credentials.json").read_text())

client = pronotepy.Client.token_login(**credentials)

if client.logged_in: # check if client successfully logged in

    # save new credentials - IMPORTANT
    credentials = client.export_credentials()
    Path("credentials.json").write_text(json.dumps(credentials))

    nom_utilisateur = client.info.name # get users name
    print(f'Logged in as {nom_utilisateur}')

    # get the all the periods (may return multiple types like trimesters and
    # semesters but it doesn't really matter the api will get it anyway)
    periods = client.periods

    for period in periods:
        for grade in period.grades:  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20
```

For any extra details, please see the documentation linked above.

## Contributing

Feel free to contribute anything. Any help is appreciated. To contribute, please create a pull request with your changes.

Setting up the development environment is just cloning the repository and making sure you have all the dependencies by
running pip with the `requirements.txt` file. Please also install `mypy` and `black` for type checking and formatting respectively.
You can find out how mypy is ran in github actions by looking at its configuration file.

If you have any questions about ENTs and their authentification function, please contact [Bapt5](https://github.com/Bapt5)

Please run these tools before you submit your PR. Thanks!

## Adding content

Pronotepy has most of the essential features covered, but if you need anything that is not yet implemented, you 
can [create an issue](https://github.com/bain3/pronotepy/issues/new) with your request. (or you can contribute by adding it yourself)

## Funding

This repository is on [issuehunt](https://issuehunt.io/r/bain3/pronotepy). You can put bounties on your issues if you'd like 
to thank the person who completes it. There is no project account for recieving tips, but you're welcome to tip contributors directly.

## License

This project uses the MIT license. (see LICENSE file)
