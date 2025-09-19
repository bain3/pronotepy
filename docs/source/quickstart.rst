Quickstart
==========

Installation
------------

You can install pronotepy v3 from the ``v3`` branch on GitHub:

.. code-block:: sh

   pip install git+https://github.com/bain3/pronotepy.git@v3

Usage
-----

Create a :class:`.Client`, which is a single authenticated session to PRONOTE.
It is created with the :meth:`.Client.login` method.

.. code-block:: python

    from pronotepy import Client, UserPass, Spaces
    
    async def main():
        credentials = UserPass(
            "https://demo.index-education.net/pronote/",
            Spaces.STUDENT,
            "demonstration",
            "pronotevs",
        )

        client = await Client.login(credentials)

        # You can now use the client. Don't forget to close it!

        async with client: # or run `await client.close()` when you're done
            print(f"The school year starts on {client.first_day}")

    asyncio.run(main())

You can get the URL for your PRONOTE instance by logging in with your
web-browser, then copying the URL from the address bar, and finally removing
the part after the last slash. If the URL in the address bar is
``https://abcd.your-schoool.invalid/some/path/pronote/parent.html``, then the
base URL is ``https://abcd.your-schoool.invalid/some/path/pronote/``.

.. note:: Authenticating to PRONOTE is a bit complicated. See :ref:`logging-in`
   for more methods and a more detailed explanation.

Grades
^^^^^^
To access the user's grades you need to first get a school term. This can be
done with :attr:`.Client.terms` to get all terms or
:attr:`.Client.current_term` to just get the current one.

.. code-block:: python

    async with client:
        # print all the grades the user had in this school year
        for period in client.terms:
            # Iterate over all the terms the user has. This includes semesters and trimesters.
            grades, *_ = await term.grades()
            for grade in grades:
                print(f"{grade.grade}/{grade.out_of}")

        # print only the grades from the current period
        grades, *_ = await client.current_term.grades()
        for grade in grades:
            print(f"{grade.grade}/{grade.out_of}")

Other usage
^^^^^^^^^^^
For other usage please consult the API reference.

JSON serialization
^^^^^^^^^^^^^^^^^^

All PRONOTE objects are dataclasses. You can use :func:`dataclasses.asdict` to convert them to a 
dictionary and serialize that.

You may want to create your own serializer to serialize :mod:`datetime` objects:

.. code-block:: python

    from dataclasses import asdict
    import json

    def serializer(obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        elif isinstance(obj, datetime.date):
            return str(obj)
        elif isinstance(obj, datetime.timedelta):
            return str(obj)

    for term in client.terms:
        print(json.dumps(asdict(term), default=serializer, indent=2))
