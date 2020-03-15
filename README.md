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

## Introduction

This is a Python API wrapper for the PRONOTE student administration service. Every function was tested on a student account, but the API should support teacher, parent or any other account. This project does **not** use the HYPERPLANNING API provided by PRONOTE, because its main goal is to make programming with PRONOTE a lot easier for students who are still learning.

## About

### Dependencies

 - pycryptodome
 - beautifulsoup4
 - requests

### Installation
**Stable**

Install directly from pypi using pip: `pip install pronotepy` 

**Latest**

1. clone this repository
2. run `pip install .` in the root directory

I cannot assure that the latest version will be working.

#### Testing the package
To self test pronotepy run this command:

`python -m pronotepy.test_pronotepy`

### Usage
Here is an example script (example.py):
```python
import pronotepy

# initialise the client
# Note: the address should be a direct one (like the one below) usually the address shown by your school just redirects
# you to the real one.
# Ex.: https://your-school.com/pronote/students <-- BAD
#      https://0000000a.index-education.net/pronote/eleve.html <-- GOOD

client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html')

if client.login('demonstration', 'pronotevs'):  # login() returns bool that signifies if it successfully logged itself in

    # get the all the periods (may return multiple types like trimesters and semesters but it doesn't really matter
    # the api will get it anyway)
    periods = client.periods

    for period in periods:
        for grade in period.grades:  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20
```

For any extra details, please see the documentation linked above.

### ENT

Pronotepy has builtin functions for getting cookies from some ENTs (if you want your ENT to be supported please contact Xiloe (see contact)). You can use those functions like this:
```python
import pronotepy
from pronotepy.ent import occitanie_montpellier

# creating the client and using the occitanie_montpellier function to automatically get cookies from ENT
client = pronotepy.Client('https://somepronote.index-education.net/pronote/eleve.html', ent=True, cookies=occitanie_montpellier('user', 'pass'))

# check if sucessfully logged in
if client.logged_in:
    print(len(client.messages())) # printing number of messages that the user has
else:
    print('no login')
```
All the functions return cookies needed to connect to pronote (use docs to see if your ENT is supported).

## License

Copyright (c) 2020 bain, Xiloe

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Contact (discord)
```plaintext
bain#5038
Xiloe#3042 (Contact me for ENT issues)
```
