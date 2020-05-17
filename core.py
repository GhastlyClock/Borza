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
        string = '/uporabnik/{0}/'.format(stanje)

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
    

@get('/uporabnik/<stanje>/')
def uporabnik(stanje):
    ukaz2 = ("SELECT * FROM UPORABNIK WHERE id = (%s)")
    cur.execute(ukaz2,(stanje, ))
    for a,b,c,d,e in cur:
        id = a
        ime = b
        priimek = c
        drzava = d
        racun = e
    ukaz4 = ("SELECT SUM(znesek) FROM TRANSAKCIJE WHERE uporabnik = (%s)")
    cur.execute(ukaz4, (racun, ))
    for x in cur:
        vrednost = x[0]
    ukaz3 = ("SELECT * FROM TRANSAKCIJE WHERE uporabnik = (%s) AND TIP = 0 ORDER BY id DESC LIMIT 20")
    cur.execute(ukaz3,(racun, ))
    trans = cur.fetchall()
    ukaz5 = ("SELECT * FROM TRANSAKCIJE WHERE uporabnik = (%s) AND TIP = 1 ORDER BY id DESC LIMIT 20")
    cur.execute(ukaz5,(racun, ))
    trans_delnice = cur.fetchall()
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

def doloci_geslo(st):
    ukaz = ("SELECT geslo FROM PRIJAVA WHERE id = (%s)")
    cur.execute(ukaz,(st, ))
    geslo = cur.fetchone()
    return geslo[0]

def stanje_racun(st):
    racun = doloci_racun(st)
    ukaz4 = ("SELECT SUM(znesek) FROM TRANSAKCIJE WHERE uporabnik = (%s)")
    cur.execute(ukaz4, (racun, ))
    vrednost = cur.fetchone()
    return vrednost[0]


@get('/uporabnik/<stanje>/denar/')
def denar(stanje):
    vrednost = stanje_racun(stanje)
    return template('denar.html', vrednost = vrednost, stanje = stanje, napaka = 0)

@post('/uporabnik/<stanje>/denar/')
def denarovanje(stanje):
    vrednost = stanje_racun(stanje)
    try:
        dvig = int(request.forms.get('kolicina1'))
        polog = int(request.forms.get('kolicina2'))
        if dvig == 0 and polog == 0:
            return template('denar.html', vrednost = vrednost, stanje = stanje, napaka = 2)
    except:
        return template('denar.html', vrednost = vrednost, stanje = stanje, napaka = 2)
    znesek = polog - dvig
    prob  = vrednost + znesek
    if prob < 0:
        return template('denar.html', vrednost = vrednost, stanje=stanje, napaka=4, prob = prob)
    geslo = request.forms.get('geslo')
    if geslo != doloci_geslo(stanje):
        return template('denar.html', vrednost = vrednost, stanje = stanje, napaka = 1)
    cur.execute("SELECT nextval('trans_id')")
    trid = cur.fetchone()
    print(trid)
    ukaz = ('INSERT INTO TRANSAKCIJE(id,znesek,uporabnik,tip) VALUES ((%s), (%s), (%s), 0)')
    cur.execute(ukaz, (trid[0], znesek, doloci_racun(stanje)))
    redirect ('/uporabnik/{0}'.format(stanje))

def vredost_delnic(st):
    ukaz = ("SELECT oznaka, sum(kolicina) FROM TRANSAKCIJE WHERE uporabnik = (%s) AND tip = 1 GROUP BY oznaka")
    racun = doloci_racun(st)
    vrednost = 0
    cur.execute(ukaz, (racun, ))
    delnice = cur.fetchall()
    for oznaka, kolicina in delnice:
        ukaz = ("SELECT cena FROM DELNICE where oznaka = (%s)")
        cur.execute(ukaz,(oznaka, ))
        cena  = cur.fetchone()
        vrednost += cena[0]*kolicina
    return vrednost

@get('/uporabnik/<stanje>/trgovanje/')
def pregled_delnic(stanje):
    ukaz = ("SELECT oznaka, sum(kolicina) FROM TRANSAKCIJE WHERE uporabnik = (%s) AND tip = 1 GROUP BY oznaka")
    racun = doloci_racun(stanje)
    cur.execute(ukaz, (racun, ))
    delnice = cur.fetchall()
    vrednost_portfelja = vredost_delnic(stanje)
    cur.execute("SELECT * FROM DELNICE")
    return template('delnice.html', stanje = stanje, delnice = delnice, vrednost_portfelja = vrednost_portfelja, vse = cur)

@get('/uporabnik/<stanje>/trgovanje/<oznaka>/')
def trgovanje(stanje, oznaka):
    ukaz =("SELECT cena,kolicina,ime FROM DELNICE where oznaka = (%s)")
    cur.execute(ukaz,(oznaka, ))
    podatek = cur.fetchone()
    cena = podatek[0]
    kolicina_na_voljo = podatek[1]
    ime = podatek[2]
    ukaz = ("SELECT sum(kolicina) FROM TRANSAKCIJE WHERE uporabnik = (%s) AND tip = 1 AND oznaka = (%s) GROUP BY oznaka")
    racun = doloci_racun(stanje)
    try:
        cur.execute(ukaz,(racun, oznaka))
        podatek = cur.fetchone()
        lastna_kolicina = podatek[0]
    except:
        lastna_kolicina = 0
    return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 0)

     

@post('/uporabnik/<stanje>/trgovanje/<oznaka>/')
def trg(stanje, oznaka):
    vrednost = stanje_racun(stanje)
    stanje_na_racunu = stanje_racun(stanje)
    ukaz =("SELECT cena,kolicina,ime FROM DELNICE where oznaka = (%s)")
    cur.execute(ukaz,(oznaka, ))
    podatek = cur.fetchone()
    cena = podatek[0]
    kolicina_na_voljo = podatek[1]
    ime = podatek[2]
    ukaz = ("SELECT sum(kolicina) FROM TRANSAKCIJE WHERE uporabnik = (%s) AND tip = 1 AND oznaka = (%s) GROUP BY oznaka")
    racun = doloci_racun(stanje)
    try:
        cur.execute(ukaz,(racun, oznaka))
        podatek = cur.fetchone()
        lastna_kolicina = podatek[0]
    except:
        lastna_kolicina = 0
    geslo = request.forms.get('geslo')
    try:
        kolicina1 = int(request.forms.get('kolicina1'))
        kolicina2 = int(request.forms.get('kolicina2'))
        prodajna_kolicina = -kolicina2
    except:
        return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1)
    if kolicina1 == 0 and kolicina2 == 0:
        return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1)

    if kolicina1 != 0 and kolicina2 != 0:
        return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 3)

    if geslo != doloci_geslo(stanje):
        return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 2)

    

    if kolicina1 == 0 and lastna_kolicina + prodajna_kolicina >= 0:
        cur.execute("SELECT nextval('trans_id')")
        trid = cur.fetchone()
        ukaz = ('INSERT INTO TRANSAKCIJE(id,znesek,uporabnik,oznaka,kolicina,tip) VALUES ((%s), (%s), (%s), (%s), (%s), 1)')
        cur.execute(ukaz,(trid[0],-prodajna_kolicina*cena,doloci_racun(stanje),oznaka, prodajna_kolicina, ))
        string = '/uporabnik/{0}/'.format(stanje)
        redirect(string)

    if kolicina1 == 0 and lastna_kolicina + prodajna_kolicina < 0:
        return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1)
    
    if kolicina2 == 0 and kolicina_na_voljo - kolicina1 >= 0:
        if stanje_na_racunu - cena*kolicina1 < 0:
            return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1)
        cur.execute("SELECT nextval('trans_id')")
        trid = cur.fetchone()
        ukaz = ('INSERT INTO TRANSAKCIJE(id,znesek,uporabnik,oznaka,kolicina,tip) VALUES ((%s), (%s), (%s), (%s), (%s), 1)')
        cur.execute(ukaz,(trid[0], -kolicina1*cena, doloci_racun(stanje), oznaka, kolicina1, ))
        string = '/uporabnik/{0}/'.format(stanje)
        redirect(string)
    if kolicina2 == 0 and kolicina_na_voljo - kolicina1 < 0:
        return template('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1)

    


baza = psycopg2.connect(database=db, host=host, user=user, password=password)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)


run(host='localhost', port=8080, reloader=True)

