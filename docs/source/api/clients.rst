Clients
=======

.. currentmodule:: pronotepy

Pronotepy currently implements three separate clients:

- :class:`.Client` - for student users

- :class:`.ParentClient` - for parent users 
  (contains additional methods for switching between kids: :meth:`.ParentClient.set_child`)

- :class:`.VieScolaireClient` - for vie scolaire users (has access to completely different resources)

All of the clients extend a :class:`.ClientBase` class, which itself does not do
much, and mainly just provides login and raw communication between pronotepy and the 
PRONOTE server.

When you make a new client instance it automatically logs in. The login process can raise a
:class:`.CryptoError` exception, which usually means that the password was incorrect.
You can check if the client is logged in using the :attr:`.ClientBase.logged_in` attribute.

Example of client initialisation:

.. code-block:: python

    import pronotepy

    try:
        client = pronotepy.Client(
            'https://demo.index-education.net/pronote/eleve.html',
            username='demonstration',
            password='pronotevs',
        )
        print(client.start_day)
    except pronotepy.CryptoError:
        exit(1)  # the client has failed to log in

    if not client.logged_in:
        exit(1)  # the client has failed to log in

.. note:: See :ref:`ent` for an example with an ENT / CAS.

-----------------------------------------------------------------------

.. autoclass:: ClientBase
    :members:

.. autoclass:: Client
    :members:
    :show-inheritance:

.. autoclass:: ParentClient
    :members:
    :show-inheritance:

.. autoclass:: VieScolaireClient
    :members:
    :show-inheritance:
