from functools import partial

# we need to ignore this because we are
# ignoring the entire generic_func.py module
from .generic_func import (  # type: ignore
    _cas,
    _cas_edu,
    _open_ent_ng_edu,
    _open_ent_ng,
    _wayf,
    _oze_ent,
    _simple_auth,
)

"""CAS"""

ac_clermont_ferrand = partial(
    _cas,
    url="https://cas.ent.auvergnerhonealpes.fr/login?selection=CLERMONT-ATS_parent_eleve",
)

ac_grenoble = partial(
    _cas,
    url="https://cas.ent.auvergnerhonealpes.fr/login?selection=GRE-ATS_parent_eleve",
)

ac_lyon = partial(
    _cas,
    url="https://cas.ent.auvergnerhonealpes.fr/login?selection=LYON-ATS_parent_eleve",
)

cas_agora06 = partial(_cas, url="https://cas.agora06.fr/login?selection=ATS-NICE")

cas_arsene76 = partial(
    _cas, url="https://cas.arsene76.fr/login?selection=ATS_parent_eleve"
)

cas_cybercolleges42 = partial(
    _cas, url="https://cas.cybercolleges42.fr/login?selection=ATS_parent_eleve"
)

cas_ent27 = partial(_cas, url="https://cas.ent27.fr/login?selection=ATS_parent_eleve")

cas_seinesaintdenis = partial(
    _cas,
    url="https://cas.webcollege.seinesaintdenis.fr/login?selection=ATS_parent_eleve",
)

cas_kosmos = partial(_cas, url="https://cas.kosmoseducation.com/login")

ecollege_haute_garonne = partial(
    _cas, url="https://cas.ecollege.haute-garonne.fr/login?selection=ATS_parent_eleve"
)
ent_creuse = partial(_cas, url="https://cas.entcreuse.fr/login")

occitanie_toulouse = partial(
    _cas, url="https://cas.mon-ent-occitanie.fr/login?selection=TOULO-ENT_parent_eleve"
)

occitanie_montpellier = partial(
    _cas, url="https://cas.mon-ent-occitanie.fr/login?selection=CSES-ENT_parent_eleve"
)

val_doise = partial(_cas, url="https://cas.moncollege.valdoise.fr/login")

"""CAS with EduConnect"""

ac_orleans_tours = partial(
    _cas_edu,
    url="https://ent.netocentre.fr/cas/login?&idpId=parentEleveEN-IdP",
    redirect_form=False,
)

cas_agora06_educonnect = partial(
    _cas_edu, url="https://cas.agora06.fr/login?selection=EDU"
)

cas_seinesaintdenis_edu = partial(
    _cas_edu,
    url="https://cas.webcollege.seinesaintdenis.fr/login?selection=EDU_parent_eleve",
)

eclat_bfc = partial(_cas_edu, url="https://cas.eclat-bfc.fr/login?selection=EDU")

ent_auvergnerhonealpe = partial(
    _cas_edu, url="https://cas.ent.auvergnerhonealpes.fr/login?selection=EDU"
)

laclasse_educonnect = partial(
    _cas_edu, url="https://www.laclasse.com/sso/educonnect", redirect_form=False
)

monbureaunumerique = partial(
    _cas_edu, url="https://cas.monbureaunumerique.fr/login?selection=EDU"
)

ac_reims = monbureaunumerique

occitanie_montpellier_educonnect = partial(
    _cas_edu,
    url="https://cas.mon-ent-occitanie.fr/login?selection=MONT-EDU_parent_eleve",
)

"""Open ENT NG"""

ent77 = partial(_open_ent_ng, url="https://ent77.seine-et-marne.fr/auth/login")

ent_essonne = partial(
    _open_ent_ng, url="https://www.moncollege-ent.essonne.fr/auth/login"
)

ent_mayotte = partial(
    _open_ent_ng, url="https://mayotte.opendigitaleducation.com/auth/login"
)

ile_de_france = partial(_open_ent_ng, url="https://ent.iledefrance.fr/auth/login")
neoconnect_guadeloupe = partial(
    _open_ent_ng, url="https://neoconnect.opendigitaleducation.com/auth/login"
)

paris_classe_numerique = partial(
    _open_ent_ng, url="https://ent.parisclassenumerique.fr/auth/login"
)

"""Open ENT NG with EduConnect"""

ent_hdf = partial(_open_ent_ng_edu, domain="https://enthdf.fr")

ent_somme = ent_hdf

l_normandie = partial(_open_ent_ng_edu, domain="https://ent.l-educdenormandie.fr")

lyceeconnecte_aquitaine = partial(_open_ent_ng_edu, domain="https://lyceeconnecte.fr/")

"""WAYF"""

ent_elyco = partial(_wayf, domain="https://cas3.e-lyco.fr", redirect_form=False)

ent2d_bordeaux = partial(
    _wayf,
    domain="https://ds.ac-bordeaux.fr",
    entityID="https://ent2d.ac-bordeaux.fr/shibboleth",
    returnX="https://ent2d.ac-bordeaux.fr/Shibboleth.sso/Login?SAMLDS=1&target=https%3A%2F%2Fent2d.ac-bordeaux.fr%2Fargos%2Fpr%2Findex%2Findex",
)

"""OZE ENT"""

enc_hauts_de_seine = partial(_oze_ent, url="https://enc.hauts-de-seine.fr/")

ozecollege_yvelines = partial(_oze_ent, url="https://ozecollege.yvelines.fr/")

"""Simple Auth"""

atrium_sud = partial(
    _simple_auth,
    url="https://www.atrium-sud.fr/connexion/login",
    form_attr={"id": "fm1"},
)
laclasse_lyon = partial(_simple_auth, url="https://www.laclasse.com/sso/login")
