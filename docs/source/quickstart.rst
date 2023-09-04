Quickstart
==========

Installation
------------
To make pronotepy's installation as easy as possible it is uploaded to pypi. To
install it you can use pip.

``pip install -U pronotepy``

If you want to install the latest version, you can install it directly from the
master branch:

``pip install -U git+https://github.com/bain3/pronotepy.git``

.. note:: You may have problems while installing the dependency pycryptodome.
   Unfortunately I haven't found a different cryptographic library, if you have
   an alternative please contact bain (see contact).

Usage
-----

Client initialisation
^^^^^^^^^^^^^^^^^^^^^
The client can be created in multiple ways. They differ only by login method.

Logging in with QR code (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. (one time setup) Obtain credentials by using ``python3 -m pronotepy.create_login``. You can either:

   1. Generate a QR code in PRONOTE and scan its contents so that you can paste them into the script, or

   2. log in using username and password. You may have to find an appropriate
      ENT function in :doc:`api/ent`. (see logging in with username and
      password below)

   The script uses :meth:`.ClientBase.qrcode_login` internally. You can generate
   new QR codes using :meth:`.ClientBase.request_qr_code_data`.

2. Create a :class:`.Client` using :meth:`.ClientBase.token_login`, passing in the credentials generated in the first step.

   .. code-block:: python
    
    import pronotepy

    client = pronotepy.Client.token_login(
        "https://demo.index-education.net/pronote/mobile.eleve.html?login=true",
        "demonstration",
        "SUPER_LONG_TOKEN_ABCDEFG",
        "RandomGeneratedUuid",
    )
    # save new credentials
    credentials = {
        "url": client.pronote_url,
        "username": client.username,
        "password": client.password,
        "uuid": client.uuid,
    }
    ...

   .. warning:: Save your new credentials somewhere safe. PRONOTE generates a
      new password token after each login.


Logging in with username and password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can also create a new client by passing in your username and password. This
needs to go through your ENT everytime you login. Consider logging in using the
QR code method.

Use an ENT function from :doc:`api/ent` if you are logging in through an ENT.

.. note:: The URL passed into the client must be a direct one to your pronote
   instance. It usually ends with ``eleve.html``, ``parent.html``, or something
   similar. Do not include any query parameters.

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

Homework
^^^^^^^^
To access the user's homework use the :meth:`.Client.homework` method.

.. code-block:: python

    import datetime
    homework = client.homework(datetime.date.today()) # this will return all the homework starting from <today>
    # homework is a list of pronotepy.Homework

Grades
^^^^^^
To access the user's grades you need to first get a period. This can be done
with the :attr:`.Client.periods` or :attr:`.Client.current_period` properties.

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
**From version 1.1 pronotepy will reinitialise the connection when the old one
expires**. This is done so bots that are checking pronote will not have to do
this manually.

Unfortunately PRONOTE changes all of its ids for their objects every session.
This makes old pronotepy objects ( :class:`.Lesson` for example) expire too.

The old data like the description or the subject will still be accessible, but
any functions that request from pronote will not work (pronotepy will raise the
:class:`.ExpiredObject` exception). To make sure that you don't get any errors
you can check the session with :meth:`.Client.session_check` and request new
objects before you make any requests using your old objects.

Below you can see sample code for a bot that checks one specific lesson content
(useless but good for this example).

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

JSON serialization
^^^^^^^^^^^^^^^^^^
Pronotepy currently supports serialization to a python :class:`dict` for easier
further processing. The built in :mod:`json` module cannot serialize
:mod:`datetime` objects, so a ``default`` function must be passed to :func:`json.dumps`.

An example showing serialization of :class:`.Period` into JSON, including
properties, because :attr:`.Period.grades` is a property, but also excluding
:attr:`.Period.punishments`:

.. code-block:: python

    import pronotepy
    import datetime
    import json
    
    # initialising the client
    client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html',
                              username='demonstration',
                              password='pronotevs')

    def serializer(obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        elif isinstance(obj, datetime.date):
            return str(obj)
        elif isinstance(obj, datetime.timedelta):
            return str(obj)

    for period in client.periods:
        serialized = period.to_dict(include_properties=True, exclude={"punishments", })
        print(json.dumps(serialized, default=serializer, indent=2))
