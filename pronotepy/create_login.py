import getpass
from typing import Optional, Type
from . import (
    Client,
    ParentClient,
    VieScolaireClient,
    ClientBase,
    MFAError,
    ent as ent_module,
)
import random
import secrets
import json


def ask_mfa() -> dict:
    print(" ! Account has higher security enabled.")

    return {
        "device_name": input(
            "Pronotepy will register as a device. Please provide a name: "
        ),
        "account_pin": input("Account PIN (leave blank if none): ") or None,
    }


def get_client_class(url: str) -> Optional[Type[ClientBase]]:
    if url.endswith("eleve.html"):
        return Client
    elif url.endswith("parent.html"):
        return ParentClient
    elif url.endswith("viescolaire.html"):
        return VieScolaireClient
    else:
        print("Unsupported client type :(")
        return None


def main() -> int:
    raw_json = input("JSON QR code contents (leave blank for user/pass login): ")

    mfa = None

    if raw_json:
        qr_code = json.loads(raw_json)
        pin = input("QR code PIN: ")

        client_class = get_client_class(qr_code["url"])
        if not client_class:
            return 1
    else:
        print()
        print("Please input the full url ending with eleve/parent.html")
        url = input("URL of your pronote instance: ")

        client_class = get_client_class(url)
        if not client_class:
            return 1

        ent_name = input("Your ENT (name of an ENT function, or leave empty): ")

        ent = getattr(ent_module, ent_name, None)
        if ent_name and not ent:
            print(
                f'Could not find ENT "{ent_name}". Pick one from https://pronotepy.rtfd.io/en/stable/api/ent.html'
            )
            return 1

        username = input("Your login username: ")
        password = getpass.getpass("Your login password: ")

        try:
            client = client_class(url, username, password, ent)
        except MFAError:
            mfa = ask_mfa()

            client = client_class(url, username, password, ent, **mfa)

        # lol
        pin = "".join([str(random.choice(tuple(range(1, 10)))) for _ in range(4)])

        qr_code = client.request_qr_code_data(pin)

    uuid = input(
        "Application UUID, preferably something random (leave blank for random): "
    ) or secrets.token_hex(8)

    try:
        client = client_class.qrcode_login(qr_code, pin, uuid)
    except MFAError:
        mfa = mfa if mfa else ask_mfa()

        client = client_class.qrcode_login(qr_code, pin, uuid, **mfa)

    print("\nCredentials:\n")
    print(json.dumps(client.export_credentials(), indent=2))
    print()
    print(
        "Log in using Client.token_login and do not forget to get new\n"
        "credentials using Client.export_credentials every session.\n"
        "\n"
        "Ex:\n\n"
        "import pronotepy\n"
        "creds = ...\n"
        f"client = pronotepy.{client_class.__name__}.token_login(**creds)\n\n"
        "creds = client.export_credentials() # new credentials\n"
    )

    return 0


if __name__ == "__main__":
    exit(main())
