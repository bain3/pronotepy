import asyncio
from pronotepy import Client, UserPass, Spaces

async def main():
    credentials = UserPass(
        "https://demo.index-education.net/pronote/",
        Spaces.STUDENT,
        "demonstration",
        "pronotevs",
    )

    client = await Client.login(credentials)

    # You can now use the client. Don't forget to close it!

    # async with client: # or run `await client.close()` when you're done
    #     print(client.start_day)
    async with client:
        # print all the grades the user had in this school year
        for term in client.terms:
            # Iterate over all the periods the user has. This includes semesters and trimesters.

            grades, *_ = await term.grades()
            for grade in grades: # the grades property returns a list of pronotepy.Grade
                print(f"{grade.grade}/{grade.out_of}") # This prints the actual grade. Could be a number or for example "Absent" (always a string)

        # print only the grades from the current period
        grades, *_ = await client.current_term.grades()
        for grade in grades:
            print(f"{grade.grade}/{grade.out_of}")

asyncio.run(main())
