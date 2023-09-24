# PRONOTE protocol

This document describes the communication protocol used by PRONOTE. All communication is JSON and HTTP(S) based, except for the initial HTML request.

- All URLs in this document are on a single host. A demo version of PRONOTE can be found at https://demo.index-education.net/pronote/
- Any information in this document is subject to change. Everything was gathered through looking at the client-side javascript and network traffic between PRONOTE and a browser.

## PRONOTE root

You can find the PRONOTE root on a server by looking at your browser URL when connected to a space (espace):

```
https://your-host.com/pronote/eleve.html -> https://your-host.com/pronote/
https://pronote.example.fr/my/path/parent.html -> https://pronote.example.fr/my/path/
```

When visiting the PRONOTE root in a web browser, it should return a page for connection to different spaces.

For the rest of this document, we'll be using `/pronote/` as the root. Not specifying the host.

## Session creation

### Step 1

To create a **desktop** session, make a `GET` request to any of the following paths, depending on the space you're connecting to:

- `/pronote/direction.html`
- `/pronote/professeur.html`
- `/pronote/viescolaire.html`
- `/pronote/parent.html`
- `/pronote/accompagnant.html`
- `/pronote/eleve.html`
- `/pronote/entreprise.html`
- `/pronote/academie.html`
- `/pronote/inscription.html`

For a **mobile** session, the HTML document name should have a `mobile.` prefix:

- `/pronote/mobile.direction.html`
- `/pronote/mobile.professeur.html`
- `/pronote/mobile.viescolaire.html`
- `/pronote/mobile.parent.html`
- `/pronote/mobile.accompagnant.html`
- `/pronote/mobile.eleve.html`
- `/pronote/mobile.entreprise.html`
- `/pronote/mobile.academie.html`
- `/pronote/mobile.inscription.html`

The request must have an up-to-date user agent header, otherwise PRONOTE will return HTML telling the client is incompatible.

A successful response will be HTML with a generated session id and other parameters telling the client how the PRONOTE instance is set up in the body element's `onload` attribute.

```html
<!DOCTYPE html>
<html lang="fr" xmlns="http://www.w3.org/1999/xhtml">
 <head>
  ...
 </head>
 <body id="id_body" role="application" onload="try { Start ({h:'2052117',sCrA:true,sCoA:true,a:3,d:true}) } catch (e) { messageErreur (e) } " class="EspaceIndex">
  ...
 </body>
</html>
```

Parameters in `onload` (`{h:'2052117',sCrA:true,sCoA:true,a:3,d:true}`):

- `h`: session id, a unique number (received as a string) identifying the current session
- `sCrA`: skip request encryption. (`true` - do not encrypt, `false` - encrypt) More information in the [encryption](#encryption) section.
- `sCoA`: skip request compression. (`true` - do not compress, `false` - compress) More information in the [compression](#compression) section.
- `a`: id of the espace (eleve, professeur, vie scolaire, ...), a number
- `d`: optional boolean, if exists and true it's a demo version of PRONOTE

### Step 2

We can now make another request to gather more information about the school and the PRONOTE instance.

```http
POST /pronote/appelfonction/<espace_id>/<session_id>/<numero_ordre>

{
    "nom": "FonctionParametres",
    "session": "<session_id>", // int
    "numeroOrdre": "<numero_ordre>",
    "donneesSec": {
        "donnees": {
            "Uuid": "...",
            "identifiantNav": "..."
        }
    }
}
```

#### numeroOrdre

A `numeroOrdre` is created by encrypting the message number (as a string) (starting from 1) with AES.

##### AES default parameters

- mode: CBC, 256 bit, using PKCS7 style padding (probably default)

- key: empty MD5 hash (`d41d8cd98f00b204e9800998ecf8427e`)
- iv: all zeroes

The first `numeroOrdre` is always `3fa959b13967e0ef176069e01e23c8d7` since the message number is 1, and AES has default parameters. You can use this to check your implementation.

The server responds with another `numeroOrdre`. It is recommended to check this value by trying to decrypt it. The result should be a number 1 larger than what you sent.
You must increment the message number by 2 every request, since responses to requests are counted, too.

#### POST data
- `Uuid` - new IV for AES encryption.
  1. **HTTPS connections**: base-64 encoded raw bytes of the IV (`b64encode(new_iv_bytes)`)
  2. **HTTP connections**: RSA encrypted and base-64 encoded raw bytes of a new *cryptographically random* IV for AES encryption (`b64encode(pcks1_v1.5(new_iv_bytes))`).

     The RSA standard used is `PCKS #1 v1.5`.
     The keys for RSA encryption are hard-coded inside the client-side javascript, and do not change between PRONOTE instances. As of the 9th of September 2023 the keys are (in decimal / base-10):
     ```
     MODULO: 130337874517286041778445012253514395801341480334668979416920989365464528904618150245388048105865059387076357492684573172203245221386376405947824377827224846860699130638566643129067735803555082190977267155957271492183684665050351182476506458843580431717209261903043895605014125081521285387341454154194253026277
     EXPONENT: 65537
     key size: 1024 bits
     ```
     You can find new keys inside `eleve.js` by searching for `c_rsaPub_modulo_1024`.

  This new IV will be used immediately by the server, including the response to this request. All new cipher texts (like `numeroOrdre`) must be created using this new IV.

- `identifiantNav` - identification string for the current client. Can be null.

#### Response

A successful response will look like this:

```json
{
    "nom": "FonctionParametres",
    "session": "<session_id>", // int
    "numeroOrdre": "<n_ordre_made_with_new_iv>",
    "donneesSec": {
        "donnees": {
            ...
        },
        "nom": "FonctionParametres"
    }
}
```

The response will have a lot of useful information about the school, the timetable, and different settings. But most importantly it has now set up the encryption IV for the current session.

## Login

There are multiple ways to log in:
 - Using (ENT generated) username and password
 - Using a QR code token, see [QR code login](#qr-code-login) for more information
 - Using a mobile application token, see [QR code login](#qr-code-login) for more information

### Step 1

First the client needs to send an identification request.

```http
POST /pronote/appelfonction/<espace_id>/<session_id>/<numero_ordre>

{
    "nom": "Identification",
    "session": "<session_id>", // int
    "numeroOrdre": "<numero_ordre>",
    "donneesSec": {
        "donnees": {
            "genreConnexion": "<connection_type>", // int
            "genreEspace": "<espace_id>", // int
            "identifiant": "<username>",
            "pourENT": false,
            "enConnexionAuto": false,
            "demandeConnexionAuto": false,
            "demandeConnexionAppliMobile": false,
            "demandeConnexionAppliMobileJeton": false,
            "enConnexionAppliMobile": false,
            "uuidAppliMobile": "",
            "loginTokenSAV": ""
        }
    }
}

```

- `connection_type` - used by accounts with multiple "types" of connection like a professor's account. (0 - domicile, 1 - dans la classe) (0 by default)

Depending on how you're logging in, you must set the appropriate booleans to `true`:
 - Username and password: `pourENT` if connecting with ENT generated credentials
 - QR code: `demandeConnexionAppliMobile` and `demandeConnexionAppliMobileJeton`
 - Mobile application token (using `jetonConnexionAppliMobile`): `enConnexionAppliMobile`

A successful response will look like:

```json
{
    "nom": "Identification",
    "session": "<session_id>", // int
    "numeroOrdre": "<numero_ordre>",
    "donneesSec": {
        "donnees": {
            "alea": "<random_string>",
            "modeCompMdp": 0,
            "modeCompLog": 0,
            "challenge": "<challenge_string>"
        },
        "nom": "Identification"
    }
}
```

- `random_string` - string used in the challenge, can be empty (missing)
- `challenge_string` - challenge for authentication

`modeCompMdp` and `modeCompLog` are integers (1 or 0 - booleans), telling the client whether to put the username (`modeCompLog == 1`) or password (`modeCompMdp == 1`) into lowercase before completing the challenge.

### Step 2

The client now needs to solve the challenge by:

1. Decoding the `challenge_string` from hex to bytes, and decrypting it with AES with the following parameters:

   - mode: CBC, 256-bit, using PKCS7 style padding (probably default)

   - key: An MD5 hash of the username, and `mtp` concatenated into a single string.

     `mtp` is an UPPERCASE hex representation of a SHA256 hash of `random_string` and the user password concatenated into a single string.

     `mtp`: `upper_case(hex(sha256(random_string+user_password)))`

     key: `md5(username+mtp)`

   - iv: same as the one communicated in session creation

1. Modifying the plain text by removing every second character.

   Examples: `abcdefg` -> `aceg`, `hello_world` -> `hlowrd`

2. Encrypting the modified text back with AES (same parameters as in 1.) and encoding it as hex

### Step 3

The client now sends the challenge back.

```http
POST /pronote/appelfonction/<espace_id>/<session_id>/<numero_ordre>

{
    "nom": "Authentification",
    "numeroOrdre": "<numero_ordre>",
    "session": "<session_id>", // int
    "donneesSec": {
        "donnees": {
            "connexion": 0,
            "challenge": "<solved_challenge>",
            "espace": "<espace_id>" // int
        }
    }
}
```

A successful response will look like this:

```json
{
    "nom": "Authentification",
    "session": "<session_id>", // int
    "numeroOrdre": "<numero_ordre>",
    "donneesSec": {
        "donnees": {
            "libelleUtil": "<name_of_user>",
            "cle": "<long_cle_string>",
            "derniereConnexion": {
                ...
            },
            "jetonConnexionAppliMobile": "LONG_TOKEN",
            ...
        },
        "nom": "Authentification"
    }
}
```

`long_cle_string` is now used to get the new AES encryption key:

1. Decode from hex and decrypt `long_cle_string` using same AES parameters that were used for solving the challenge in the previous step. The output is a string of comma separated numbers (`"10,2,159,23,54,78,..."`).

2. Convert the obtained string into the actual bytes. (separate numbers by commas, and parse them for their actual value)

   Python example: `bytes([int(i) for i in long_cle_string.split(",")])`

3. Make an MD5 hash of the bytes. This is the new key.

**The client is now logged in. The session is authenticated and the encryption has been set up.**

## Getting general user data and settings - ParametresUtilisateur

The client can get user data (which is **required for some requests**) with a request, like so:

```http
POST /pronote/appelfonction/<espace_id>/<session_id>/<numero_ordre>

{
    "nom": "ParametresUtilisateur",
    "numeroOrdre": "<numero_ordre>",
    "session": "<session_id>", // int
    "donneesSec": {}
}
```

One interesting part of the response is the `ressource` which describes the user that the info should be connected to. It is used extensively in parent accounts to control multiple children.

## Compression

Data compression is only done for the contents of `donneesSec`. **It is done before encryption.**

1. Get data in JSON form, as a UTF-8 string (usually already in that encoding anyways)
2. Compress the string with zlib (compression level 6, without any headers - just raw compressed data)
3. *If compression is done without encrypting, convert the output to hex. The hex string is the `donneesSec` value.*

## Encryption

Just like for compression, only the `donneesSec` contents are encrypted.

1. There are two possible inputs
   1. Data is compressed. In that case work with the compressed bytes.
   2. Data is uncompressed. Convert data to a JSON string, work with the UTF-8 bytes of that string (just like compression) (unverified)
2. Encrypt with the same encryption used for `numeroOrdre`.
3. Convert output to hex. The web client also makes it all uppercase but it might not be necessary.

## ENT

Connecting through an ENT is usually just a matter of sending a request to the ENT with your user credentials, which gives you cookies that
are then used in the initial request for the pronote HTML. The `onload` attribute will have more information, more specifically
keys: `e` and `f`. `e` is used as a replacement for the username, and `f` for the password. 

When solving the login challenge when connecting through an ENT, decrypt with AES parameters like this:

- mode: CBC, 256-bit, using PKCS7 style padding (probably default)

- key: An MD5 hash of the hex of a SHA256 hash of the password

  `md5(upper_case(hex(sha256(password))))`

- iv: same as the one communicated in session creation

## QR code login

> See [Androz2091's explanation](https://github.com/Androz2091/pronote-qrcode-api) for even more information.

A QR code generated from PRONOTE will contain the following JSON:
```json
{
    "login": "SOME_HEX_STRING",
    "jeton": "ANOTHER_HEX_STRING",
    "url": "/pronote/mobile.espace.html"
}
```
The `login` and `jeton` keys are encrypted using AES with the following parameters:
 - mode: CBC, 256-bit
 - key: MD5 hash of the pin code (as a string) (`md5(pin)`)
 - iv: all zeroes

The QR code credentials are valid for **10 minutes**.

After decrypting the username (`login`) and password (`jeton`), use the credentials to log in.

For the initial request of the HTML page, append a `?login=true`, so PRONOTE doesn't redirect you to your ENT. You also need to create a
UUID (any random string), which needs to identify your application, and must **not** change between logins. You must send the UUID in
the `Identification` request, in `uuidAppliMobile`.

You will get a new password token in the `Authentification` response, in `jetonConnexionAppliMobile`. You can
directly use this password token to log in again. The next login will be to `url?login=true`, using `login` as the username,
`jetonConnexionAppliMobile` as the password, and using the same UUID as the initial QR code login.

## Getting the timetable - PageEmploiDuTemps

To get timetable information of a certain week, use this request:

```http
POST /pronote/appelfonction/<espace_id>/<session_id>/<numero_ordre>

{
    "nom": "PageEmploiDuTemps",
    "numeroOrdre": "<numero_ordre>",
    "session": "<session_id>", // int
    "donneesSec": {
    	"donnees": {
            "ressource": "<ressource>", // dict
            "Ressource": "<ressource>", // dict
            "numeroSemaine": "<n_semaine>", // int
            "NumeroSemaine": "<n_semaine>", // int
            "avecAbsencesEleve": false,
            "avecConseilDeClasse": true,
            "estEDTPermanence": false,
            "avecAbsencesRessource": true,
            "avecDisponibilites": true,
            "avecInfosPrefsGrille": true
    	},
    	"_Signature_": {
    		"onglet": 16
    	}
        
    }
}
```

- `ressource` and `Ressource` - this is received as part of the `ParametresUtilisateur` request, the web clients uses directly the dict it received

- `numeroSemaine` and `NumeroSemaine` - this is the week that the client is looking for.

  It is calculated like this: `1 + int((date - start_day).days / 7)`.

  Where `date` is some date int the week the client is looking for, and `start_day` is the starting day of the school year (received in `FonctionParametres` request).

## Getting grades for a certain school period

1. Get data about a certain school period. This object will be later called `p`. You can get all the school periods from the `FonctionParametres` request.

2. Make this request

   ```http
   POST /pronote/appelfonction/<espace_id>/<session_id>/<numero_ordre>
   
   {
       "nom": "DernieresNotes",
       "numeroOrdre": "<numero_ordre>",
       "session": "<session_id>", // int
       "donneesSec": {
           "donnees": {
               "periode": {
               	"N": "<p.N>", // int
               	"L": "<p.L>"
               }
           },
           "_Signature_": {
           	"onglet": 198
           }
       }
   }
   ```

## Getting other information from PRONOTE

The PRONOTE system is way too big to describe all requests you can make. With this document you will be able to log in, and figure out the basic inner workings of the system. I recommend using your browser's dev tools, and looking at the requests sent when browsing PRONOTE to figure out how to get other data. I wish you good luck and lots of patience :)
