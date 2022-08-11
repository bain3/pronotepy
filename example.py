import pronotepy
import datetime
# initialise the client
# Note: the address should be a direct one (like the one below) usually the address shown by your school just redirects
# you to the real one.
# Ex.: https://your-school.com/pronote/students <-- BAD
#      https://0000000a.index-education.net/pronote/eleve.html <-- GOOD
#      https://0000000a.index-education.net/pronote/eleve.html?login=true <-- ONLY IF YOU HAVE AN ENT AND YOU KNOW YOUR IDS, ELSE REFER TO ENT PART OF README
client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html',
                          username='demonstration',
                          password='pronotevs')

if client.logged_in: # check if client successfully logged in
    # get the all the periods (may return multiple types like trimesters and semesters but it doesn't really matter
    # the api will get it anyway)
    nom_utilisateur = client.info.name # get users name
    print(f'Logged in as {nom_utilisateur}')
    
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
    
