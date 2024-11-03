"""
Objectif de l'exemple :
   - Parcours des données du trimestre en cours
   - Conversion avec la présentation d'un bulletin possible
        (poles qui regroupent les matières) ('class Bulletin')
   - Affichage d'une IHM qui représente le bulletin
        (codage par classe et héritage) ('class Application')
   - Applications de rêgles pour gagner une récompense/cagnotte ('class Rules')
   - Définir une configuration de récompense/cagnotte (JSON pour 'class Rules')
               - Banco : Récompense sur un trimestre
               - Boost : Multiplicateur de gain sur un pôle
               - Marathon : Récompense cumulée sur plusieurs trimestres
   - Définir une configuration de description d'un bulletin (JSON pour 'class Bulletin')
               - Poles de disciplines
               - Moyennes par pole
   - TODO : Affichage dans l'IHM de l'état de gain de la récompense et du niveau de la cagnotte
   - TODO : Affichage spécifique BANCO
   - TODO : Affichage spécifique BOOST
   - TODO : Affichage spécifique MARATHON
"""

import sys
from pathlib import Path
import json

import pronotepy

from example_5.bulletin import Bulletin
from example_5.rules import Rules
from example_5.application import Application


# load login from `python3 -m pronotepy.create_login` command
# See quickstart in documentation for other login methods.
credentials = json.loads(Path("credentials.json").read_text(encoding='utf-8'))

client = pronotepy.Client.token_login(**credentials)

if client.logged_in:  # check if client successfully logged in

    # save new credentials - IMPORTANT
    credentials = client.export_credentials()
    Path("credentials.json").write_text(
        json.dumps(credentials), encoding='utf-8')

    nom_utilisateur = client.info.name  # get users name
    print(f'Logged in as {nom_utilisateur}')

    current_period = client.current_period

    bulletin_actuel = Bulletin(Path('example_5', 'bulletin.json'))
    bulletin_actuel.compute_pole_averages(current_period.averages)
    bulletin_actuel.compute_pole_delays(current_period.delays)

    ps5_rules = Rules(Path('example_5', 'rules.json'))

    fenetre = Application(ps5_rules, bulletin_actuel)
    fenetre.mainloop()

else:
    print("Failed to log in")
    sys.exit()
