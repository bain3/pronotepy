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

> **Note**
> If you are on Windows and have trouble with this command, use `py -3 -m pip install pronotepy`. You must have Python 3 installed on your machine.

#### Latest

You can install the latest version by installing directly from the repository:

`pip install -U git+https://github.com/bain3/pronotepy`

We cannot assure that the latest version will be working, but it might have features or bugfixes that are not yet released on pypi.

### Testing the package
To self test pronotepy run this command:

`python -m pronotepy.test_pronotepy`

*Please keep in mind that this uses the demo version of pronote and so it can't test every function.*

### Usage

> **Warning**
>
> The usage part of this readme is for the latest version. If you are installing from pypi, please see the documentation linked at the beginning.

Here is an example script (homework shown in example.py):
```python
import pronotepy

# initialise the client
# Note: the address should be a direct one (like the one below) usually the address shown by your school just redirects
# you to the real one.
# Ex.: https://your-school.com/pronote/students <-- BAD
#      https://0000000a.index-education.net/pronote/eleve.html <-- GOOD
#      https://0000000a.index-education.net/pronote/eleve.html?login=true <-- ONLY IF YOU HAVE AN ENT AND YOU KNOW YOUR IDS, ELSE REFER TO ENT PART OF README

client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html',
                          username='demonstration',
                          password='pronotevs')

if client.logged_in: # check if client successfully logged in
    # get the all the periods (may return multiple types like trimesters and semesters but it doesn't really matter
    # the api will get it anyway)
    periods = client.periods

    for period in periods:
        for grade in period.grades:  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20
```

For any extra details, please see the documentation linked above.

### QR Code

Pronotepy allows you to connect with the Pronote QR code. Pass in the function the contents of the QR code and the confirmation code
```python
import pronotepy

# creating the client from qrcode_login
client = pronotepy.Client.qrcode_login({"jeton":"<LONG_TOKEN>",
                                        "login":"<SHORT_TOKEN>",
                                        "url":"https://0000000a.index-education.net/pronote/mobile.eleve.html"},
                                        "1234")
```

### ENT

Pronotepy has builtin functions for getting cookies from some ENTs (if you want your ENT to be added make a new issue).
You can pass those functions to the client like this:

```python
import pronotepy
from pronotepy.ent import occitanie_montpellier

# creating the client and passing the occitanie_montpellier function to automatically get cookies from ENT
client = pronotepy.Client('https://0000000a.index-education.net/pronote/eleve.html',
                          username='demonstration',
                          password='pronotevs',
                          ent=occitanie_montpellier)

# check if sucessfully logged in
if client.logged_in:
    print(len(client.discussions())) # printing number of messages that the user has
else:
    print('no login')
```

All the functions return cookies needed to connect to pronote (use docs to see if your ENT is supported).

## Contributing

Feel free to contribute anything. Any help is appreciated. To contribute, please create a pull request with your changes.

Setting up the development environment is just cloning the repository and making sure you have all the dependencies by
running pip with the `requirements.txt` file. Please also install `mypy` and `black` for type checking and formatting respectively.
You can find out how mypy is ran in github actions by looking at its configuration file.

Please run these tools before you submit your PR. Thanks!

## Adding content

Pronotepy has most of the essential features covered, but if you need anything that is not yet implemented, you 
can [create an issue](https://github.com/bain3/pronotepy/issues/new) with your request. (or you can contribute by adding it yourself)

## Funding

This repository is on [issuehunt](https://issuehunt.io/r/bain3/pronotepy). You can put bounties on your issues if you'd like 
to thank the person who completes it. There is no project account for recieving tips, but you're welcome to tip contributors directly.

## License

This project uses the MIT license. (see LICENSE file)
