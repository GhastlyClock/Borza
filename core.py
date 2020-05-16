from bottle import *
import requests
from auth_public import *


import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki

debug(True)

stanje = 0

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
    redirect('/zacetna_stran/')

@get('/prijava/')
def prijava():
    global stanje
    if stanje !=0:
        redirect('/zacenta_stran/')
    napaka = 0
    return template('prijava.html', napaka=napaka, stanje = stanje)



def preveri_uporabnika(ime,geslo):
    ukaz = ("SELECT geslo FROM PRIJAVA WHERE mail = (%s)")
    cur.execute(ukaz,(ime, ))
    for passw in cur:
        if passw[0] == geslo:
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
        global stanje 
        stanje = uid
        string = '/uporabnik/{0}'.format(stanje)
        print(stanje)
        redirect(string)
#        return template('uporabnik.html', id = id, ime = ime, priimek=priimek, drzava = drzava, racun = racun, trans = cur, stanje = stanje)
    else:
        return template('prijava.html', napaka = 1, stanje = stanje)

@get('/registracija/')
def register():
    global stanje 
    if stanje !=0:
        redirect('/zacetna_stran/')
    return template('registracija.html', stanje = stanje, napaka = 0)

#def pridobi_podatke(stevilo):
#    ukaz2 = ("SELECT * FROM UPORABNIK WHERE id = (%s)")
#        cur.execute(ukaz2,(stevilo, ))
#        for a,b,c,d,e in cur:
#            id = a
#            ime = b
#            priimek = c
#            drzava = d
#            racun = e
#    ukaz3 = ("SELECT * FROM TRANSAKCIJE WHERE uporabnik = (%s)")
#    cur.execute(ukaz3,(racun, ))
    

@get('/uporabnik/<stanje>')
def uporabnik(stanje):
    ukaz2 = ("SELECT * FROM UPORABNIK WHERE id = (%s)")
    cur.execute(ukaz2,(stanje, ))
    for a,b,c,d,e in cur:
        id = a
        ime = b
        priimek = c
        drzava = d
        racun = e
    ukaz4 = ("SELECT SUM(znesek) FROM TRANSAKCIJE WHERE uporabnik = (%s) AND TIP = 0")
    cur.execute(ukaz4, (racun, ))
    for x in cur:
        vrednost = x[0]
    ukaz3 = ("SELECT * FROM TRANSAKCIJE WHERE uporabnik = (%s) AND TIP = 0 ORDER BY id DESC LIMIT 20")
    cur.execute(ukaz3,(racun, ))
    trans = cur.fetchall()
    ukaz5 = ("SELECT * FROM TRANSAKCIJE WHERE uporabnik = (%s) AND TIP = 1 ORDER BY id DESC LIMIT 20")
    cur.execute(ukaz5,(racun, ))
    trans_delnice = cur.fetchall()
    print(trans_delnice)
    return template('uporabnik.html', stanje = stanje, id=a, ime=b, priimek = c, drzava = d, racun  =e, trans=trans, vrednost = vrednost, trans_delnice = trans_delnice)



@post('/registracija/')
def registracija():
    ime = request.forms.get('ime')
    priimek = request.forms.get('priimek')
    email = request.forms.get('mail')
    drzava = request.forms.get('drzava')
    trr = request.forms.get('trr')
    geslo1 = request.forms.get('pass1')
    geslo2 = request.forms.get('pass2')
    if ime is '' or priimek is '' or email is '' or drzava is '' or trr is '' or geslo1 is '' or geslo2 is '':
        return template('registracija.html', stanje= stanje, napaka = 1)
    string = 'SELECT mail FROM PRIJAVA'
    cur.execute(string)
    stevec = 0
    for x in cur:
        if x[0] == email:
            return template('registracija.html', stanje = stanje, napaka = 2)
        else: 
            continue
    string = 'SELECT racun FROM UPORABNIK'
    cur.execute(string)
    for x in cur:
        if x[0] == trr:
            return template('registracija.html', stanje = stanje, napaka=3)
        else:
            continue
    if len(geslo1) < 6:
        return template('registracija.html', stanje = stanje, napaka =5)
    if geslo1 == geslo2:
        cur.execute("SELECT nextval('zaporedje_uporabnik')")
        for x in cur:
            uid = x[0]
        ukaz_reg = ('INSERT INTO UPORABNIK(id,ime,priimek,drzava,racun) VALUES ((%s), (%s), (%s), (%s), (%s))')
        cur.execute(ukaz_reg,(uid, ime, priimek, drzava, trr, ))

        ukaz_pri = ('INSERT INTO PRIJAVA(id, mail, geslo) VALUES ((%s), (%s), (%s))')
        cur.execute(ukaz_pri, (uid, email, geslo1, ))
        string = '/uporabnik/{0}'.format(uid)
        redirect(string)
    else:
        return template('registracija.html', stanje = stanje, napaka = 4)


def doloci_racun(st):
    ukaz2 = ("SELECT racun FROM UPORABNIK WHERE id = (%s)")
    cur.execute(ukaz2,(st, ))
    racun = cur.fetchone()
    return racun[0]




@get('/uporabnik/<stanje>/denar/')
def denar(stanje):
    racun = doloci_racun(stanje)
    ukaz4 = ("SELECT SUM(znesek) FROM TRANSAKCIJE WHERE uporabnik = (%s) AND TIP = 0")
    cur.execute(ukaz4, (racun, ))
    for x in cur:
        vrednost = x[0]
    return template('denar.html', vrednost = vrednost)

@post('/uporabniki/<stanje>/denar/')
def denarovanje(stanje):
    return



baza = psycopg2.connect(database=db, host=host, user=user, password=password)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)


run(host='localhost', port=8080, reloader=True)

