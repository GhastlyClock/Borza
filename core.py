from bottle import *
import requests
from auth_public import *

import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki

debug(True)

stanje = 1

#Popravek problema, ko bottle ne najde templatea
def bottle_monkeypatch():
    """
    This adds /common folder to bottle template path, thus
    makes templating cleaner and more manageable.
    """
    from bottle import TEMPLATE_PATH
    global TEMPLATE_PATH
    TEMPLATE_PATH.insert(0, './views')

# Mapa za statične vire (slike, css, ...)
static_dir = "./static"

#Izracun vrednosti skupka delnic
def izracun(cur):
    stevec = 0
    for a,b,cena,c, kolicina in cur:  
        stevec += kolicina*cena 
    return stevec

@route("/static/<filename:path>")
def static(filename):
    return static_file(filename, root=static_dir)

@get('/')
def index():
    return template('zacetna_stran.html', stanje = stanje)

@get('/zacetna_stran/')
def zacetna_get():
    return template('zacetna_stran.html', stanje = stanje)

@get('/borze/')
def borze():
    cur.execute("""SELECT * FROM BORZE""")
    return template('borze.html', borze=cur, stanje = stanje)

@get('/borze/<oznaka>')
def borza(oznaka):
    ukaz = ("SELECT oznaka,ime,cena,sektor,kolicina FROM DELNICE WHERE borza = (%s)")
    cur.execute(ukaz,(oznaka, ))
    vrednost= izracun(cur)
    cur.execute(ukaz,(oznaka, ))
    return template('borze_podrobno.html', delnice=cur, oznaka=oznaka, vrednost=vrednost, stanje = stanje)



@get('/sektorji/')
def sektorji():
    cur.execute("SELECT id,ime_sektorja,cena_mrd FROM SEKTOR")
    return template('sektorji.html', sektorji=cur, stanje = stanje)

@get('/sektorji/<oznaka>')
def sektor(oznaka):
    ukaz=("SELECT oznaka,ime,cena,borza,kolicina FROM DELNICE WHERE sektor = (%s)")
    cur.execute(ukaz,(oznaka, ))
    vrednost = izracun(cur)
    cur.execute(ukaz,(oznaka, ))
    return template('sektor_podrobno.html',sektor=cur,oznaka=oznaka, vrednost=vrednost, stanje = stanje)

@get('/topdelnice/')
def delnice():
    cur.execute('SELECT * FROM DELNICE ORDER BY cena DESC LIMIT 20')
    return template('topdelnice.html', delnice=cur, stanje = stanje)

@get('/odjava/')
def odjava():
    global stanje
    stanje = 0
    return template('zacetna_stran.html', stanje = stanje)

@get('/prijava/')
def prijava():
    napaka = 0
    return template('prijava.html', napaka=napaka, stanje = stanje)



def preveri_uporabnika(ime,geslo):
    ukaz = ("SELECT mail FROM PRIJAVA WHERE geslo = (%s)")
    cur.execute(ukaz,(geslo, ))
    for mail in cur:
        if mail[0] == ime:
            return True
        else:
            return False

@post('/prijava/')
def prijavljanje():
    ime = request.forms.get('mail')
    geslo = request.forms.get('geslo')
    if preveri_uporabnika(ime,geslo):
        ukaz1 = ("SELECT id FROM PRIJAVA WHERE geslo = (%s) AND mail = (%s)")
        cur.execute(ukaz1, (geslo,ime, ))
        for id in cur:
            uid = id[0]
        ukaz2 = ("SELECT * FROM UPORABNIK WHERE id = (%s)")
        cur.execute(ukaz2,(uid, ))
        for a,b,c,d,e in cur:
            id = a
            ime = b
            priimek = c
            drzava = d
            racun = e
        ukaz3 = ("SELECT * FROM TRANSAKCIJE WHERE uporabnik = (%s)")
        cur.execute(ukaz3,(racun, ))
        global stanje 
        stanje = id
        return template('uporabnik.html', id = id, ime = ime, priimek=priimek, drzava = drzava, racun = racun, trans = cur, stanje = stanje)
    else:
        return template('prijava.html', napaka = 1, stanje = stanje)

@get('/registracija/')
def register():
    return template('registracija.html', stanje = stanje)

baza = psycopg2.connect(database=db, host=host, user=user, password=password)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)


run(host='localhost', port=8080, reloader=True)

