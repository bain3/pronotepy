.. _ent:

ENT / CAS
=========

All ENT functions that you can use while initialising the client:

An example of client initialisation with the ac_reunion ENT.

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

ac_clermont_ferrand
~~~~~~~~~~~~~~~~~~~
.. autofunction:: ac_clermont_ferrand

ac_grenoble
~~~~~~~~~~~
.. autofunction:: ac_grenoble

ac_lyon
~~~~~~~
.. autofunction:: ac_lyon

ac_orleans_tours
~~~~~~~~~~~~~~~~
.. autofunction:: ac_orleans_tours

ac_poitiers
~~~~~~~~~~~
.. autofunction:: ac_poitiers

ac_reims
~~~~~~~~
.. autofunction:: ac_reims

ac_rennes
~~~~~~~~~
.. autofunction:: ac_rennes

ac_reunion
~~~~~~~~~~
.. autofunction:: ac_reunion

atrium_sud
~~~~~~~~~~
.. autofunction:: atrium_sud

cas_agora06
~~~~~~~~~~~
.. autofunction:: cas_agora06

cas_arsene76
~~~~~~~~~~~~
.. autofunction:: cas_arsene76

cas_cybercolleges42
~~~~~~~~~~~~~~~~~~~
.. autofunction:: cas_cybercolleges42

cas_ent27
~~~~~~~~~
.. autofunction:: cas_ent27

cas_kosmos
~~~~~~~~~~
.. autofunction:: cas_kosmos

cas_seinesaintdenis
~~~~~~~~~~~~~~~~~~~
.. autofunction:: cas_seinesaintdenis

cas_seinesaintdenis_edu
~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: cas_seinesaintdenis_edu

eclat_bfc
~~~~~~~~~
.. autofunction:: eclat_bfc

ecollege_haute_garonne
~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: ecollege_haute_garonne

enc_hauts_de_seine
~~~~~~~~~~~~~~~~~~
.. autofunction:: enc_hauts_de_seine

ent2d_bordeaux
~~~~~~~~~~~~~~
.. autofunction:: ent2d_bordeaux

ent77
~~~~~
.. autofunction:: ent77

ent_auvergnerhonealpe
~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: ent_auvergnerhonealpe

ent_creuse
~~~~~~~~~~
.. autofunction:: ent_creuse

ent_elyco
~~~~~~~~~
.. autofunction:: ent_elyco

ent_essonne
~~~~~~~~~~~
.. autofunction:: ent_essonne

ent_hdf
~~~~~~~
.. autofunction:: ent_hdf

ent_mayotte
~~~~~~~~~~~
.. autofunction:: ent_mayotte

ent_somme
~~~~~~~~~
.. autofunction:: ent_somme

ent_var
~~~~~~~
.. autofunction:: ent_var

ile_de_france
~~~~~~~~~~~~~
.. autofunction:: ile_de_france

l_normandie
~~~~~~~~~~~
.. autofunction:: l_normandie

laclasse_educonnect
~~~~~~~~~~~~~~~~~~~
.. autofunction:: laclasse_educonnect

laclasse_lyon
~~~~~~~~~~~~~
.. autofunction:: laclasse_lyon

lyceeconnecte_aquitaine
~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: lyceeconnecte_aquitaine

monbureaunumerique
~~~~~~~~~~~~~~~~~~
.. autofunction:: monbureaunumerique

neoconnect_guadeloupe
~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: neoconnect_guadeloupe

occitanie_montpellier
~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: occitanie_montpellier

occitanie_montpellier_educonnect
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: occitanie_montpellier_educonnect

occitanie_toulouse
~~~~~~~~~~~~~~~~~~
.. autofunction:: occitanie_toulouse

ozecollege_yvelines
~~~~~~~~~~~~~~~~~~~
.. autofunction:: ozecollege_yvelines

paris_classe_numerique
~~~~~~~~~~~~~~~~~~~~~~
.. autofunction:: paris_classe_numerique

val_doise
~~~~~~~~~
.. autofunction:: val_doise

