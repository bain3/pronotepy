import getpass
from . import Client, ent as ent_module
import random
import secrets
import json


def main() -> int:
    raw_json = input("JSON QR code contents (leave blank for user/pass login): ")

    if raw_json:
        qr_code = json.loads(raw_json)
        pin = input("QR code PIN: ")
    else:
        print()
        print("Please input the full url ending with eleve/parent.html")
        url = input("URL of your pronote instance: ")

        ent_name = input("Your ENT (name of an ENT function, or leave empty): ")

        ent = getattr(ent_module, ent_name, None)
        if ent_name and not ent:
            print(
                f'Could not find ENT "{ent_name}". Pick one from https://pronotepy.rtfd.io/en/stable/api/ent.html'
            )
            return 1

        username = input("Your login username: ")
        password = getpass.getpass("Your login password: ")

        client = Client(url, username, password, ent)

        # lol
        pin = "".join([str(random.choice(tuple(range(1, 10)))) for _ in range(4)])

        qr_code = client.request_qr_code_data(pin)

    uuid = input(
        "Application UUID, preferably something random (leave blank for random): "
    ) or secrets.token_hex(8)

    client = Client.qrcode_login(qr_code, pin, uuid)

    print("\nCredentials:\n")
    print("Server URL:", client.pronote_url)
    print("Username:", client.username)
    print("Password:", client.password)
    print("UUID:", client.uuid)
    print()
    print(
        "Log in using Client.token_login and do not forget to keep the new client.password after each login"
    )

    return 0


if __name__ == "__main__":
    exit(main())
