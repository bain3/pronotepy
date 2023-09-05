.. _ent:

ENT / CAS
=========

All ENT functions that you can use while initializing the client.

An example of client initialization with the ac_reunion ENT:

.. code-block:: python

   from pronotepy import Client
   from pronotepy.ent import ac_reunion

   client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html',
                      username='demonstration',
                      password='pronotevs',
                      ent=ac_reunion)

.. note:: All ENT functions just return cookies received from their ENT. You can create
   your own function with the following signature: ``(username: str, password: str) -> RequestsCookieJar``,
   and use it for ENTs that have not been implemented.

-----------------------------------------------------------------

.. currentmodule:: pronotepy.ent

.. autofunction:: cas_kosmos

.. autofunction:: ent_creuse

.. autofunction:: occitanie_toulouse

.. autofunction:: occitanie_montpellier

.. autofunction:: val_doise

.. autofunction:: cas_cybercolleges42_edu

.. autofunction:: ecollege_haute_garonne_edu

.. autofunction:: ac_orleans_tours

.. autofunction:: ac_poitiers

.. autofunction:: ac_reunion

.. autofunction:: cas_agora06

.. autofunction:: cas_seinesaintdenis_edu

.. autofunction:: cas_arsene76_edu

.. autofunction:: eclat_bfc

.. autofunction:: ent_auvergnerhonealpe

.. autofunction:: laclasse_educonnect

.. autofunction:: monbureaunumerique

.. autofunction:: occitanie_montpellier_educonnect

.. autofunction:: occitanie_toulouse_edu

.. autofunction:: ent77

.. autofunction:: ent_essonne

.. autofunction:: ent_mayotte

.. autofunction:: ile_de_france

.. autofunction:: neoconnect_guadeloupe

.. autofunction:: paris_classe_numerique

.. autofunction:: lyceeconnecte_aquitaine

.. autofunction:: ent_94

.. autofunction:: ent_hdf

.. autofunction:: ent_somme

.. autofunction:: ent_var

.. autofunction:: l_normandie

.. autofunction:: lyceeconnecte_edu

.. autofunction:: ent_elyco

.. autofunction:: atrium_sud

.. autofunction:: laclasse_lyon

.. autofunction:: extranet_colleges_somme
