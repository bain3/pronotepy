"""
Objectif de l'exemple :
   - Parcours des données du trimestre en cours
   - Conversion avec la présentation d'un bulletin possible
        (poles qui regroupent les matières) ('class ReportCard')
   - Affichage d'une IHM qui représente le bulletin
        (codage par classe et héritage) ('class Application')
   - Applications de rêgles pour gagner une récompense/cagnotte ('class Rules')
   - Définir une configuration de récompense/cagnotte (JSON pour 'class Rules')
               - Banco : Récompense sur un trimestre
               - Boost : Multiplicateur de gain sur un pôle
               - Marathon : Récompense cumulée sur plusieurs trimestres
   - Définir une configuration de description d'un bulletin (JSON pour 'class ReportCard')
               - Poles de disciplines
               - Moyennes par pole
   - Affichage dans l'IHM de l'état de gain de la récompense et du niveau de la cagnotte
   - Affichage spécifique BANCO
   - Affichage spécifique BOOST
   - Affichage spécifique MARATHON
"""

import sys
from pathlib import Path
import json

import pronotepy

from example_5.report_card import ReportCard
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

    username = client.info.name  # get users name
    print(f'Logged in as {username}')

    current_period = client.current_period

    current_report_card = ReportCard(Path('example_5', 'report_card.json'))
    current_report_card.compute_report_card_averages(current_period.averages)
    current_report_card.compute_report_card_delays(current_period.delays)

    school_award_rules = Rules(Path('example_5', 'rules.json'))

    fenetre = Application(school_award_rules, current_report_card)
    fenetre.mainloop()

else:
    print("Failed to log in")
    sys.exit()
