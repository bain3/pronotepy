# api-pronote

## Introduction

This is a Python API wrapper for the PRONOTE service. Every function was tested on a student account, but the API should support teacher, parent or any other account. Any functions which are not accessible by the students are not yet supported. This project does **not** use the HYPERPLANNING API provided by PRONOTE, because its main goal is to make programming with PRONOTE a lot easier for students who are still learning.

## About

### Dependencies

 - cryprodome
 - beautifulsoup4
 - requests

### Small example

This is an example code of the user accessing all of his grades:

```python
import apipronote

# initialise the client
# Note: the address should be a direct one (like the one below) usually the address shown by your school just redirects
# you to the real one.
# Ex.: https://your-school.com/pronote/students <-- BAD
#      https://0000000a.index-education.net/pronote/eleve.html <-- GOOD

client = apipronote.Client('https://0000000a.index-education.net/pronote/eleve.html')

if client.login('username', 'password'):  # login() returns bool that signifies if it successfully logged itself in

    # get all the periods (may return multiple types like trimesters and semesters but it doesn't really matter
    # the api will get it anyway)
    periods = client.periods()

    for period in periods:
        for grade in period.grades():  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20
```

### API Reference

#### `apipronote.Client(pronote_url)`<a name="client"></a>

**Parameters**

- `pronote_url` (***str***) -

  String of a url of a PRONOTE server. MUST be a direct url, most schools make a redirect on their page to the pronote servers, because the hostname of the server is ugly. Redirects don't work with this API because the html is modified.

  - https://0000000a.index-education.net/pronote/eleve.html

    this is a good url

  - https://your-school.com/pronote/students

    this is a bad url beacuse it redirects the user (if your school hosts its own PRONOTE server, then it could work)

  The best way get a good URL is to check where the web browser makes all its POST requests.

##### `login(username, password)`

Logs in as with the passed credentials. The password is not stored in the memory for long, it is immediately deleted after it has been used.

- ***Parameters***

  - `username `(***str***) -

    Username of the user.

  - `password `(***str***) -

    Password of the user.

- ***Returns***

  **bool** - True if the user was successfully logged in and False if not.

##### `periods()`

Gets all the periods of the school year. Will return semesters and trimesters.

- ***Returns***

  List[[apipronote.Period](#apipronoteperiod)] - list of all the periods obtained

##### `current_period()`

Gets the current periods. Will return semesters and trimesters.

- ***Returns***

  List[[apipronote.Period](#apipronoteperiod)] - list of all the current periods

##### `homework(date_from, date_to = None)`

Returns all homework in the given timespan. If `date_to` is `None` , it will return all homework from `date_from` until the end of the year.

- ***Parameters***

  - `date_from` ([***datetime.date***](https://docs.python.org/2/library/datetime.html#datetime.date)) -

    The first time boundary.

  - `date_to` ([***datetime.date***](https://docs.python.org/2/library/datetime.html#datetime.date)) -

    The second time boundary.

- ***Returns***

  List[[apipronote.Homework](#apipronotehomework)] - Homework given between the two time boundaries.

##### `lessons(date_from, date_to = None)`

Returns all lessons in the given timespan. If `date_to` is `None`, it will return lessons only from the `date_from` day.

**This function may return pedagogical outings, in which case the returned `Lesson` will only have `start` and `outing` attributes set!**

- ***Parameters***

  - `date_from` ([***datetime.date***](https://docs.python.org/2/library/datetime.html#datetime.date)) -

    The first time boundary.

  - `date_to` ([***datetime.date***](https://docs.python.org/2/library/datetime.html#datetime.date)) -

    The second time boundary.

- ***Returns***

  List[[apipronote.Lesson](#apipronotelesson)] - Lessons between the two time boundaries.

  

#### `apipronote.Grade`

Represents a grade. You shouldn't have to initialise this class manually.

##### `id`

***str*** - id of the grade (used internally)

##### `grade`

***str*** - actual grade

##### `out_of`

***str*** - maximum amount of points

##### `default_out_of`

***str*** - default maximum amount of points

##### `date`

[***datetime.date***](https://docs.python.org/2/library/datetime.html#datetime.date) - date on which the grade was given

##### `course`

***[apipronote.Course](#apipronotecourse)*** (only partially attributed) - course in which the grade was given 

##### `period`

***[apipronote.Period](#apipronoteperiod)*** - period in which the grade was given

##### `average`

***str*** - average grade of the class

##### `max`

***str*** - highest grade of the test

##### `min`

***str*** - lowest grade of the test

##### `coefficient`

***str*** - coefficient of the grade



#### `apipronote.Course`

Represents a course. You shouldn't have to initialise this class manually.

##### `id`

***str*** - id of the course (used internally)

##### `name`

***str*** - name of the course

##### ***---  all attributes under this may not be present at all times  ---***

##### `groups`

***bool*** - if the course is divided into smaller groups

##### `average`

***str*** - users average in the course

##### `class_average`

***str*** - classes average in the course

##### `max`

***str*** - highest grade in the class

##### `min`

***str*** - lowest grade in the class

##### `out_of`

***str*** - maximum amount of points

##### `default_out_of`

***str*** - default maximum amount of points



#### `apipronote.Lesson`

Represents a lesson with a given time. You shouldn't have to create this class manually.

**If a lesson is a pedagogical outing, it will only have the `outing` and `start` attributes**

##### `id`

***str*** - id of the lesson (used internally)

##### `course`

***[apipronote.Course](#apipronotecourse)*** (only partially attributed) - course that the lesson is from

##### `teacher_name`

***str*** - name of the teacher

##### `classroom`

***str*** - name of the classroom

##### `canceled`

***bool*** - if the lesson is canceled

##### `outing`

***bool*** - if it is a pedagogical outing

##### `start`

[***datetime.datetime***](https://docs.python.org/2/library/datetime.html#datetime.datetime) - starting time of the lesson



#### `apipronote.Homework`

Represents a homework. You shouldn't have to create this class manually.

##### `id`

***str*** - id of the homework (used internally)

##### `course`

[***apipronote.Course***](#apipronotecourse) (only partially attributed) - course that the homework is for

##### `description`

***str*** - description of the homework

##### `done`

***bool*** - if the homework is marked done

##### `set_done(status)`

Changes the status of the homework (done or not done).

- ***Patameters***

  - `status` (***bool***) -

    To which status to change to.



#### `apipronote.Period`

Represents a homework. You shouldn't have to create this class manually.

##### `id`

***str*** - id of the period (used internally)

##### `name`

***str*** - name of the period

##### `start`

[***datetime.date***](https://docs.python.org/2/library/datetime.html#datetime.date) - date on which the period starts

##### `end`

[***datetime.date***](https://docs.python.org/2/library/datetime.html#datetime.date) - date on which the period ends

##### `grades()`

Fetches the grades from this period from the server.

- ***Returns***

  [***apipronote.Grade***](#apipronotegrade) - grades from this period

##### `averages()`

Fetches the averages from this period from the server.

- ***Returns***

  [***apipronote.Course***](#apipronotecourse) (fully attributed) - averages from this period

## License

Copyright (c) 2020, bain

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
