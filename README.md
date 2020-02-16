# pronotepy

## Introduction

This is a Python API wrapper for the PRONOTE student administration service. Every function was tested on a student account, but the API should support teacher, parent or any other account. This project does **not** use the HYPERPLANNING API provided by PRONOTE, because its main goal is to make programming with PRONOTE a lot easier for students who are still learning.

## About

### Dependencies

 - cryptodome
 - beautifulsoup4
 - requests

### Installation
 - **Stable**
 
   install with pip: `pip install pronotepy`
 - **Latest**
   1. clone this repository
   2. run `pip install .`

### Small example

This is an example code of the user accessing all of his grades:

```python
import pronotepy

# initialise the client
# Note: the address should be a direct one (like the one below) usually the address shown by your school just redirects
# you to the real one.
# Ex.: https://your-school.com/pronote/students <-- BAD
#      https://0000000a.index-education.net/pronote/eleve.html <-- GOOD

client = pronotepy.ClientStudent('https://demo.index-education.net/pronote/eleve.html')

if client.login('demonstration', 'pronotevs'):  # login() returns bool that signifies if it successfully logged itself in

    # get all the periods (may return multiple types like trimesters and semesters but it doesn't really matter
    # the api will get it anyway)
    periods = client.periods()

    for period in periods:
        for grade in period.grades:  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20
```

### [API Reference](https://github.com/bain3/pronotepy/wiki)

## License

Copyright (c) 2020 bain

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Contact
discord: `bain#5038`
