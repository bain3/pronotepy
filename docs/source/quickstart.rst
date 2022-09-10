Quickstart
==========

Installation
------------
To make pronotepy's installation as easy as possible it is uploaded to pypi. To install it you can use pip.

``pip install -U pronotepy``

If you want to install the latest version, you can install it directly from the master branch:

``pip install -U git+https://github.com/bain3/pronotepy.git``

.. note:: You may have problems while installing the dependency pycryptodome. Unfortunately I haven't found a different cryptographic library, if you have an alternative please contact bain (see contact).

Usage
-----

Client initialisation
^^^^^^^^^^^^^^^^^^^^^
To create a new client you need to create an instance and pass your pronote address, username and password.
This will initialise the connection and log the user in. You can check if the client is logged with the logged_in attribute.

.. code-block:: python

    import pronotepy
    from pronotepy.ent import ac_reunion
    # importing ent specific function, you do not need to import anything if you dont use an ent

    client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html',
                          username='demonstration',
                          password='pronotevs',
                          ent=ac_reunion) # ent specific
    if not client.logged_in:
        exit(1)  # the client has failed to log in

.. note:: Make sure that the url is directly pointing to the html file (usually schools have their pronote 
   hosted by index-education so the url will be similar to the one in the example above).

Homework
^^^^^^^^
To access the users homework use the :meth:`.Client.homework` method.

.. code-block:: python

    import datetime
    homework = client.homework(datetime.date.today()) # this will return all the homework starting from <today>
    # homework is a list of pronotepy.Homework

Grades
^^^^^^
To access the users grades you need to first get a period. This can be done with the :attr:`.Client.periods` or :attr:`.Client.current_period`
properties.

.. code-block:: python

    # print all the grades the user had in this school year
    for period in client.periods:
        # Iterate over all the periods the user has. This includes semesters and trimesters.

        for grade in period.grades: # the grades property returns a list of pronotepy.Grade
            print(grade.grade) # This prints the actual grade. Could be a number or for example "Absent" (always a string)

    # print only the grades from the current period
    for grade in client.current_period.grades:
        print(grade.grade)

Long Term Usage
^^^^^^^^^^^^^^^
From version 1.1 **pronotepy will reinitialise the connection when the old one expires**. This is done so bots that are checking pronote
will not have to do this manually.

Unfortunately **PRONOTE changes all of its ids for their objects every session**.
This makes **old pronotepy objects (** :class:`.Lesson` **for example) expire** too.

The old data like the description or the subject will still be accessible,
but any **functions that request from pronote will not work** (pronotepy will raise the :class:`.ExpiredObject` exception).
To make sure that you don't get any errors you can check the session with :meth:`.Client.session_check` and request new objects before you make any requests using your old objects.

Below you can see sample code for a bot that checks one specific lesson content (useless but good for this example).

.. code-block:: python

    import pronotepy
    import datetime
    from time import sleep

    # initialising the client
    client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html',
                              username='demonstration',
                              password='pronotevs')

    # user login check
    if not client.logged_in:
        print("Client is not logged in")
        exit()

    # getting the initial lesson
    lesson = client.lessons(client.start_day + datetime.timedelta(days=1))[0]

    while True: # infinite loop

        # Checks the session status and refreshes the session if it is expired.
        # Returns True if it has been refreshed.
        if client.session_check():

            # renew the lesson object
            lesson = client.lessons(client.start_day + datetime.timedelta(days=1))[0]

            print("Session reinitialised and object renewed.")

        # the content property sends a request to pronote asking for the content (inefficient so don't use it often)
        print(lesson.content)
        # lesson.content is pronotepy.LessonContent

        sleep(7200) # wait for 2 hours

Other usage
^^^^^^^^^^^
For other usage please consult the API reference.
