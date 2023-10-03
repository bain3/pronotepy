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

.. autofunction:: ac_orleans_tours

.. autofunction:: ac_poitiers

.. autofunction:: ac_reunion

.. autofunction:: ac_reims

.. autofunction:: ac_rennes

.. autofunction:: atrium_sud

.. autofunction:: cas_agora06

.. autofunction:: cas_arsene76_edu

.. autofunction:: cas_cybercolleges42_edu

.. autofunction:: cas_kosmos

.. autofunction:: cas_seinesaintdenis_edu

.. autofunction:: eclat_bfc

.. autofunction:: ecollege_haute_garonne_edu

.. autofunction:: ent_94

.. autofunction:: ent_auvergnerhonealpe

.. autofunction:: ent_creuse

.. autofunction:: ent_creuse_educonnect

.. autofunction:: ent_elyco

.. autofunction:: ent_essonne

.. autofunction:: ent_hdf

.. autofunction:: ent_mayotte

.. autofunction:: ent_somme

.. autofunction:: ent_var

.. autofunction:: ent77

.. autofunction:: ent_ecollege78

.. autofunction:: extranet_colleges_somme

.. autofunction:: ile_de_france

.. autofunction:: laclasse_educonnect

.. autofunction:: laclasse_lyon

.. autofunction:: l_normandie

.. autofunction:: lyceeconnecte_aquitaine

.. autofunction:: lyceeconnecte_edu

.. autofunction:: monbureaunumerique

.. autofunction:: neoconnect_guadeloupe

.. autofunction:: occitanie_montpellier

.. autofunction:: occitanie_montpellier_educonnect

.. autofunction:: occitanie_toulouse_edu

.. autofunction:: ozecollege_yvelines

.. autofunction:: paris_classe_numerique

.. autofunction:: pronote_hubeduconnect

.. autofunction:: val_de_marne

.. autofunction:: val_doise
