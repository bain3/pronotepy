from functools import partial

from .generic_func import _cas, _cas_edu, _open_ent_ng_edu, _open_ent_ng, _simple_auth

ac_clermont_ferrand = partial(
    _cas, url='https://cas.ent.auvergnerhonealpes.fr/login?selection=CLERMONT-ATS_parent_eleve')
ac_grenoble = partial(
    _cas, url='https://cas.ent.auvergnerhonealpes.fr/login?selection=GRE-ATS_parent_eleve')
ac_lyon = partial(
    _cas, url='https://cas.ent.auvergnerhonealpes.fr/login?selection=LYON-ATS_parent_eleve')
cas_agora06 = partial(
    _cas, url='https://cas.agora06.fr/login?selection=ATS-NICE')
occitanie_toulouse = partial(
    _cas, url='https://cas.mon-ent-occitanie.fr/login?selection=TOULO-ENT_parent_eleve')
occitanie_montpellier = partial(
    _cas, url='https://cas.mon-ent-occitanie.fr/login?selection=CSES-ENT_parent_eleve')
val_doise = partial(_cas, url='https://cas.moncollege.valdoise.fr/login')

ac_orleans_tours = partial(
    _cas_edu, url='https://ent.netocentre.fr/cas/login?&idpId=parentEleveEN-IdP')
cas_agora06_educonnect = partial(
    _cas_edu, url='https://cas.agora06.fr/login?selection=EDU')
eclat_bfc = partial(
    _cas_edu, url='https://cas.eclat-bfc.fr/login?selection=EDU')
ent_auvergnerhonealpe = partial(
    _cas_edu, url='https://cas.ent.auvergnerhonealpes.fr/login?selection=EDU')
monbureaunumerique = partial(
    _cas_edu, url='https://cas.monbureaunumerique.fr/login?selection=EDU')
ac_reims = monbureaunumerique
occitanie_montpellier_educonnect = partial(
    _cas_edu, url='https://cas.mon-ent-occitanie.fr/login?selection=MONT-EDU_parent_eleve')

ent77 = partial(_open_ent_ng, url='https://ent77.seine-et-marne.fr/auth/login')
ent_essonne = partial(
    _open_ent_ng, url='https://www.moncollege-ent.essonne.fr/auth/login')
ent_mayotte = partial(
    _open_ent_ng, url='https://mayotte.opendigitaleducation.com/auth/login')
ile_de_france = partial(
    _open_ent_ng, url='https://ent.iledefrance.fr/auth/login')
neoconnect_guadeloupe = partial(
    _open_ent_ng, url='https://neoconnect.opendigitaleducation.com/auth/login')
paris_classe_numerique = partial(
    _open_ent_ng, url='https://ent.parisclassenumerique.fr/auth/login')

ent_hdf = partial(_open_ent_ng_edu, domain='https://enthdf.fr')
ent_somme = ent_hdf
l_normandie = partial(
    _open_ent_ng_edu, domain='https://ent.l-educdenormandie.fr')
lyceeconnecte_aquitaine = partial(
    _open_ent_ng_edu, domain='https://lyceeconnecte.fr/')

atrium_sud = partial(
    _simple_auth, url='https://www.atrium-sud.fr/connexion/login', form_attr={'id': 'fm1'})
