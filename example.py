import pronotepy

import datetime
from pathlib import Path
import json

# load login from `python3 -m pronotepy.create_login` command
# See quickstart in documentation for other login methods.
credentials = json.loads(Path("credentials.json").read_text())

client = pronotepy.Client.token_login(**credentials)

if client.logged_in: # check if client successfully logged in

    # save new credentials - IMPORTANT
    credentials = client.export_credentials()
    Path("credentials.json").write_text(json.dumps(credentials))

    nom_utilisateur = client.info.name # get users name
    print(f'Logged in as {nom_utilisateur}')
    
    # get the all the periods (may return multiple types like trimesters and
    # semesters but it doesn't really matter the api will get it anyway)
    periods = client.periods

    for period in periods:
        for grade in period.grades:  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20

    today = datetime.date.today() # store today's date using datetime built-in library
    homework = client.homework(today) # get list of homework for today and later
    
    for hw in homework: # iterate through the list
        print(f"({hw.subject.name}): {hw.description}") # print the homework's subject, title and description
    
else: 
    print("Failed to log in")
    exit()
