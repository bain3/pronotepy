import pronotepy
import datetime
# initialise the client
# Note: the address should be a direct one (like the one below) usually the address shown by your school just redirects
# you to the real one.
# Ex.: https://your-school.com/pronote/students <-- BAD
#      https://0000000a.index-education.net/pronote/eleve.html <-- GOOD

client = pronotepy.Client('https://demo.index-education.net/pronote/eleve.html',
                          username='demonstration',
                          password='pronotevs')

if client.logged_in: #check if client successfully logged in
    # get the all the periods (may return multiple types like trimesters and semesters but it doesn't really matter
    # the api will get it anyway)
    periods = client.periods

    for period in periods:
        for grade in period.grades:  # iterate over all the grades
            print(f'{grade.grade}/{grade.out_of}')  # print out the grade in this style: 20/20

    today = datetime.date.today() #store today's date using datetime built-in library
    homework = client.homework(today) #get list of all homework which are for today and after 
    
    for hw in homework: #iterate through the list
        print(f"({hw.subject.name}): {hw.description}") #print the homework's subject, title and description

    
else: #if it didn't log in
    print("Failed to log in")
    exit()
    
