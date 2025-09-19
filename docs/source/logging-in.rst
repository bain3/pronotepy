.. _logging-in:

Logging in
==========

The different login methods Pronotepy supports are documented below. If the
account uses 2 factor authentication, see :ref:`mfa`.

Username and password
^^^^^^^^^^^^^^^^^^^^^

Simplest login method: logs in through username and password *directly* on the
PRONOTE website (not through ENT/CAS).

Here is an example on how to use the :class:`.UserPass` credentials:

.. code-block:: python

    credentials = UserPass(
        "https://demo.index-education.net/pronote/",
        Spaces.STUDENT, # or PARENT, VIESCOLAIRE
        username="demonstration",
        password="pronotevs",
    )

    client = await Client.login(credentials)

See :ref:`base-url` for an explanation of the base URL.

.. _qr-code:

QR code
^^^^^^^

All PRONOTE instances support logging in with a QR code. You can generate one
by clicking the little QR code symbol just next your name after logging into
PRONOTE.

The :class:`.QRCode` needs the *extracted contents* from the QR code. You can
do this manually by screenshotting the QR code, and reading it with some online
QR reader, for example.

Here is an example:

.. code-block:: python

   import json

   code_contents = read_the_qr_code()  # somehow get the contents

   credentials = QRCode(
       code_contents=json.loads(code_contents),
       pin="1234",
       app_uuid="SOM3TH1NG-R4ND0M",  # any random string
   )

   client = await Client.login(credentials)

The QR code is **valid for 10 minutes**, and is **single-use**.

Use :attr:`.Client.next_token` to get the credentials for the next login. They are
also single-use.

.. code-block:: python

   from dataclasses import asdict
   import json
   from pathlib import Path
   from pronotepy import Token

   client = await Client.login(qr_code_credentials)

   token = client.next_token

   # save token for later
   Path("my-token.json").write_text(json.dumps(asdict(client.next_token)))

   async with client:
      ... # do stuff

   # ... some while later

   # load the token
   token = Token(**json.loads(Path("my-token.json").read_text()))

   client = await Client.login(token)

   # again, a new token is in client.next_token, save it!


ENT/CAS cookies
^^^^^^^^^^^^^^^

This is a low-level login method. All PRONOTE instances support logging in with
:ref:`qr-code`.

After a successful login using CAS, the service will redirect you to your PRONOTE
instance with special cookies. The :class:`.CasCookies` authenticates you with them.

.. code-block:: python
   
   cookies = get_cookies_from_cas(username, password)  # somehow get cookies

   credentials = CasCookies(
      "https://your.instance.invalid/pronote/",
      Spaces.STUDENT,
      cookies,  # aiohttp.CookieJar
   )

.. _base-url:

Getting the base URL
^^^^^^^^^^^^^^^^^^^^

You can get the URL for your PRONOTE instance by logging in with your
web-browser, then copying the URL from the address bar, and finally removing
the part after the last slash. If the URL in the address bar is
`https://abcd.your-schoool.invalid/some/path/pronote/parent.html`, then the
base URL is `https://abcd.your-schoool.invalid/some/path/pronote/`.


.. _mfa:

Multi-Factor Authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If the account has 2 factor authentication, then logging in also requires
passing in a :class:`.MFACredentials` instance.

.. code-block:: python

   # First login. We need a name to register the device. This account also
   # requires a PIN.
   credentials = UserPass(...)
   mfa = MFACredentials(
      account_pin="1234",
      device_name="my-app",
   )

   client = await Client.login(credentials, mfa)

   # Save the assigned client identificator. Lets you skip 2FA next time.
   client_identificator = client.client_identificator

   # ... next time

   # Log in as the saved device
   client = await Client.login(
      credentials,
      MFACredentials(client_identificator=client_identificator),
   )
