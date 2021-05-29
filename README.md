<h2 align="center">Looking for maintainers</h2>
We (bain, Xiloe) do not actively maintain this project anymore. We would love to hear from someone who would
take on the role of a maintainer. As a last goodbye I have created a PRONOTE protocol description that describes
the login process and some inner workings of PRONOTE. It can be used as a stepping stone to create a better API wrapper,
or to start contributing to this one.

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
  [![Run Unit Tests](https://github.com/bain3/pronotepy/workflows/Run%20Unit%20Tests/badge.svg)](https://github.com/bain3/pronotepy/actions?query=workflow%3A%22Run+Unit+Tests%22)

## Introduction

This is a Python API wrapper for the PRONOTE student administration service. Every function was tested on a student account, but the API should support parent accounts, too. This project does **not** use the HYPERPLANNING API provided by PRONOTE, because its main goal is to make programming with PRONOTE a lot easier for students who are still learning.

## About

### Dependencies

 - pycryptodome
 - beautifulsoup4
 - requests

### Installation
**Stable**

Install directly from pypi using pip: `pip install pronotepy` (If you are on windows and have trouble with this command, use this one assuming you are using python 3.x.x installed on your computer: `py -3 -m pip install pronotepy`)

**Latest**

1. clone this repository
2. run `pip install .` in the root directory

I cannot assure that the latest version will be working.

#### Testing the package
To self test pronotepy run this command:

`python -m pronotepy.test_pronotepy`

*Please keep in mind that this uses the demo version of pronote
and so it can't test every function.*
### Usage

```diff
- The usage part of this readme is for the latest version, 
- if you're installing from pypi, please see the documentation. 
- It is linked right on the top of this readme.
```

Here is an example script (example.py):
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

if client.logged_in:
    # get the all the periods (may return multiple types like trimesters and semesters but it doesn't really matter
    # the api will get it anyway)
    periods = client.periods

    for period in periods:
        for grade in period.grades:  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20
```

For any extra details, please see the documentation linked above.

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
    print(len(client.messages())) # printing number of messages that the user has
else:
    print('no login')
```
All the functions return cookies needed to connect to pronote (use docs to see if your ENT is supported).

### Long Term Usage

Pronotepy will try and reconnect when the old session expires, but it cannot assure that the old objects will still be working. To prevent having problems with expired objects, please make sure that you're requesting new ones when you have long pauses in between requests to pronote.

## Contributing

Feel free to contribute anything. Any help is appreciated. To contribute, please create a pull request with your changes.

Setting up the development environment is just cloning the repository and making sure you have all the dependencies by
running pip with the requirements.txt file.

## Adding content

Pronotepy has most of the essential features covered, but if you need anything that is not yet implemented, you can [create an issue](https://github.com/bain3/pronotepy/issues/new) with your request. (or you can contribute by adding it yourself)

## License

Copyright (c) 2020-2021 bain, Xiloe

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
