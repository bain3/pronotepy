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
from datetime import datetime as dt

import pronotepy

from the_school_award.report_card import ReportCard
from the_school_award.rules import Rules
from the_school_award.application import Application

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
    user_class = client.info.class_name
    establishment = client.info.establishment
    year = client.start_day.year
    print(f'Logged in as {username} from class "{user_class}" in establishment "{establishment}" year {year}-{year+1}')

    now = dt.now()
    now_date = now.date()
    report_cards = []
    for period in client.periods:
        # Period.name : 'Trimestre x', 'Semestre x', 'Annee continue' ...
        if not period.name.startswith('Trimestre'):
            continue
        if period.start <= now:
            # Trimestre achevé ou commencé
            report_card = ReportCard(
                Path('the_school_award', 'report_card.json'))
            report_card.compute_report_card_infos(client, period)
            report_card.compute_report_card_averages(period.averages)
            report_card.compute_report_card_delays(period.delays)
            # Save period to json with date until it is over. Then save final period and stop to save.
            if now <= period.end:
                save_path = Path('the_school_award', f'report_card_{period.name.replace(' ','_')}_{now_date}.json')
                report_card.save(save_path)
            else:
                save_path = Path('the_school_award', f'report_card_{period.name.replace(' ','_')}.json')
                if not save_path.exists():
                    report_card.save(save_path)
            report_cards.append(report_card)

    school_award_rules = Rules(Path('the_school_award', 'rules.json'))

    fenetre = Application(school_award_rules, report_cards)
    fenetre.mainloop()

else:
    print("Failed to log in")
    sys.exit()
