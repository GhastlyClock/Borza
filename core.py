from bottle import *
import requests
from auth_public import *
import random
import hashlib


import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki

import os

# privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
ROOT = os.environ.get('BOTTLE_ROOT', '/')
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)


def rtemplate(*largs, **kwargs):
    """
    Izpis predloge s podajanjem spremenljivke ROOT z osnovnim URL-jem.
    """
    return template(ROOT=ROOT, *largs, **kwargs)



debug(True)

kodiranje = 'laqwXUtKfHTp1SSpnkSg7VbsJtCgYS89QnvE7PedkXqbE8pPj7VeRUwqdXu1Fr1kEkMzZQAaBR93PoGWks11alfe8y3CPSKh3mEQ'

#funkcija za piškotke
def id_uporabnik():
    if request.get_cookie("id", secret = kodiranje):
        piskotek = request.get_cookie("id", secret = kodiranje)
        return piskotek
    else:
        return 0


#Popravek problema, ko bottle ne najde templatea
import bottle
import os     
abs_app_dir_path = os.path.dirname(os.path.realpath(__file__))
abs_views_path = os.path.join(abs_app_dir_path, 'views')
bottle.TEMPLATE_PATH.insert(0, abs_views_path )

# Mapa za statične vire (slike, css, ...)
static_dir = "./static"

#Izracun vrednosti skupka delnic
def izracun(cur):
    stevec = 0
    for a,b,cena,c, kolicina in cur:  
        stevec += kolicina*cena 
    return stevec

#določimo pot
@route("/static/<filename:path>")
def static(filename):
    return static_file(filename, root=static_dir)

#z get dobimo indeks uporabnika
@get('/')
def index():
    stanje = id_uporabnik()
    return rtemplate('zacetna_stran.html', stanje = stanje)

#z get dobimo zacetno stran naše borze
@get('/zacetna_stran/')
def zacetna_get():
    stanje = id_uporabnik()
    return rtemplate('zacetna_stran.html', stanje = stanje)

#izvozimo vse borze in naredimo html
@get('/borze/')
def borze():
    stanje = id_uporabnik()
    cur.execute("""SELECT * FROM BORZE""")
    return rtemplate('borze.html', borze=cur, stanje = stanje)

@get('/borze/<oznaka>')
def borza(oznaka):
    stanje = id_uporabnik()
    ukaz = ("SELECT oznaka,ime,cena,sektor,kolicina FROM DELNICE WHERE borza = (%s)")
    cur.execute(ukaz,(oznaka, ))
    vrednost= izracun(cur)
    cur.execute(ukaz,(oznaka, ))
    return rtemplate('borze_podrobno.html', delnice=cur, oznaka=oznaka, vrednost=vrednost, stanje = stanje)



@get('/sektorji/')
def sektorji():
    stanje = id_uporabnik()
    cur.execute("SELECT id,ime_sektorja,opis FROM SEKTOR")
    return rtemplate('sektorji.html', sektorji=cur, stanje = stanje)

@get('/sektorji/<oznaka>')
def sektor(oznaka):
    stanje = id_uporabnik()
    ukaz=("SELECT oznaka,ime,cena,borza,kolicina FROM DELNICE WHERE sektor = (%s)")
    cur.execute(ukaz,(oznaka, ))
    vrednost = izracun(cur)
    cur.execute(ukaz,(oznaka, ))
    return rtemplate('sektor_podrobno.html',sektor=cur,oznaka=oznaka, vrednost=vrednost, stanje = stanje)

@get('/topdelnice/')
def delnice():
    stanje = id_uporabnik()
    cur.execute('SELECT * FROM DELNICE ORDER BY cena DESC LIMIT 20')
    return rtemplate('topdelnice.html', delnice=cur, stanje = stanje)

@get('/odjava/')
def odjava():
    response.delete_cookie("id", path='/')
    redirect('{0}zacetna_stran/'.format(ROOT))

@get('/prijava/')
def prijava():
    stanje = id_uporabnik()
    if stanje !=0:
        redirect('{0}zacetna_stran/'.format(ROOT))
    napaka = 0
    return rtemplate('prijava.html', napaka=napaka, stanje = stanje)



def preveri_uporabnika(ime,geslo):
    ukaz = ("SELECT geslo FROM novi_uporabniki WHERE mail = (%s)")
    cur.execute(ukaz,(ime, ))
    for passw in cur:
        if passw[0] == hashGesla(geslo):
            return True
        else:
            return False

def preveri_geslo(uid, geslo):
    ukaz = ('SELECT geslo FROM novi_uporabniki WHERE id = (%s)')
    cur.execute(ukaz,(uid, ))
    for x in cur:
        try:
            hashi = x[0]
        except:
            return False 
    if hashi == hashGesla(geslo):
        return True
    return False
            

def hashGesla(s):
    m = hashlib.sha256()
    m.update(s.encode("utf-8"))
    return m.hexdigest()

@post('/prijava/')
def prijavljanje():
    ime = request.forms.mail
    geslo = request.forms.geslo

    if preveri_uporabnika(ime,geslo):
        ukaz1 = ("SELECT id FROM novi_uporabniki WHERE mail = (%s)")
        cur.execute(ukaz1, (ime, ))
        for x in cur:
            uid = x[0]
        response.set_cookie("id",uid, path='/', secret = kodiranje)
        string = '{0}uporabnik/{1}/'.format(ROOT,uid)
        redirect(string)
#        return template('uporabnik.html', id = id, ime = ime, priimek=priimek, drzava = drzava, racun = racun, trans = cur, stanje = stanje)
    else:
        return rtemplate('prijava.html', napaka = 1, stanje = 0)

@get('/registracija/')
def register():
    stanje = id_uporabnik()
    if stanje !=0:
        redirect('{0}zacetna_stran/'.format(ROOT))
    polja_registracija = ("ime", "priimek", "mail", "drzava", "trr", "pass1", "pass2")
    podatki = {polje: "" for polje in polja_registracija}
    return rtemplate('registracija.html', stanje=stanje, napaka=0, **podatki)
    

@get('/uporabnik/<stanje>/')
def uporabnik(stanje):
    piskot = id_uporabnik()
    if piskot != int(stanje):
        redirect('{0}zacetna_stran/'.format(ROOT))

    ukaz2 = ("SELECT * FROM novi_uporabniki WHERE id = (%s)")
    cur.execute(ukaz2,(stanje, ))
    for a,b,c,d,e,f,g in cur:
        id = a
        ime = b
        priimek = c
        drzava = d
    
    ukaz4 = ("SELECT sum(znesek) FROM denar_transakcije where uporabnik = (%s)")
    cur.execute(ukaz4, (stanje, ))
    
    for x in cur.fetchall():
        vre = x[0]
  
    try: vrednost = round(float(vre),2)
    except: vrednost = 0


    vrednost = round(vrednost,2)
    ukaz3 = ("SELECT * FROM denar_transakcije where uporabnik = (%s) ORDER BY id DESC LIMIT 20")
    cur.execute(ukaz3,(stanje, ))
    trans = cur.fetchall()

    ukaz5 = ("SELECT * FROM delnice_transakcije WHERE uporabnik = (%s) ORDER BY id DESC LIMIT 20")
    cur.execute(ukaz5,(stanje, ))
    trans_delnice = cur.fetchall()

    stanje = id_uporabnik()
    return rtemplate('uporabnik.html', stanje = stanje, id=a, ime=b, priimek = c, drzava = d, trans=trans, vrednost = vrednost, trans_delnice = trans_delnice)



@post('/registracija/')
def registracija():
    stanje = id_uporabnik()

    polja_registracija = ("ime", "priimek", "mail", "drzava", "trr", "pass1", "pass2")
    podatki = {polje: "" for polje in polja_registracija}
    podatki = {polje: getattr(request.forms, polje) for polje in polja_registracija}

    ime = podatki.get('ime')
    priimek = podatki.get('priimek')
    email = podatki.get('mail')
    drzava = podatki.get('drzava')
    trr = podatki.get('trr')
    geslo1 = podatki.get('pass1')
    geslo2 = podatki.get('pass2')

    if ime == '' or priimek == '' or email == '' or drzava == '' or trr == '' or geslo1 == '' or geslo2 == '':
        return rtemplate('registracija.html', stanje= stanje, napaka = 1, **podatki)

    string = ('SELECT racun,mail FROM novi_uporabniki where racun = (%s) or mail = (%s)')
    cur.execute(string, (trr, email,  ))
    ujemanje = cur.fetchone()
    if ujemanje != None:
        if ujemanje[0] == trr:
            return rtemplate('registracija.html', stanje = stanje, napaka=3, **podatki)
        else:
            return rtemplate('registracija.html', stanje = stanje, napaka = 2, **podatki)

    if len(geslo1) < 6:
        return rtemplate('registracija.html', stanje = stanje, napaka =5, **podatki)
    if geslo1 == geslo2:
        podatki["geslo"] = hashGesla(podatki["pass1"])
        ukaz = """INSERT INTO novi_uporabniki (ime,priimek,drzava,racun,mail,geslo)
                  VALUES((%(ime)s), (%(priimek)s), (%(drzava)s), (%(trr)s), (%(mail)s),(%(geslo)s))
                  RETURNING id"""
        cur.execute(ukaz, podatki)
        uid = cur.fetchone()[0]
        response.set_cookie("id",uid, path='/', secret = kodiranje)
        string = '{0}uporabnik/{1}/'.format(ROOT,uid)
        redirect(string)
    else:
        return rtemplate('registracija.html', stanje = stanje, napaka = 4, **podatki)


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

def stanje_racun(stanje):
    ukaz4 = ("SELECT sum(znesek) FROM denar_transakcije where uporabnik = (%s)")
    cur.execute(ukaz4, (stanje, ))
    
    for x in cur.fetchall():
        vre = x[0]
       
    try: vrednost = round(float(vre),2)
    except: vrednost = 0
    
    return vrednost

@get('/uporabnik/<stanje>/denar/')
def denar(stanje):
    piskotek = id_uporabnik()
    if piskotek != int(stanje):
        redirect('{0}zacetna_stran/'.format(ROOT))
    vrednost = stanje_racun(stanje)
    return rtemplate('denar.html', vrednost = vrednost, stanje = stanje, napaka = 0)

@post('/uporabnik/<stanje>/denar/')
def denarovanje(stanje):
    vrednost = stanje_racun(stanje)
    try:
        kolicina = float(request.forms.kolicina1)
        vrsta = request.forms.vrsta
  
        if kolicina <=0:
            return rtemplate('denar.html', vrednost = vrednost, stanje = stanje, napaka = 2)
    except:
        return rtemplate('denar.html', vrednost = vrednost, stanje = stanje, napaka = 2)
    kolicina = round(kolicina,2)
    geslo = request.forms.geslo
    if vrsta == 'polog':
        if not preveri_geslo(stanje, geslo):
            return rtemplate('denar.html', vrednost = vrednost, stanje = stanje, napaka = 1)
        cur.execute("SELECT nextval('trans_id')")
        trid = cur.fetchone()
        ukaz = ('INSERT INTO denar_transakcije(id,znesek,uporabnik) VALUES ((%s), (%s), (%s))')
        cur.execute(ukaz, (trid[0], kolicina, stanje, ))
        redirect ('{0}uporabnik/{1}/'.format(ROOT,stanje))

    if vrsta == 'dvig':
        if not preveri_geslo(stanje, geslo):
            return rtemplate('denar.html', vrednost = vrednost, stanje = stanje, napaka = 1)
        if vrednost - kolicina < 0:
            return rtemplate('denar.html', vrednost = vrednost, stanje = stanje, napaka = 2)
        cur.execute("SELECT nextval('trans_id')")
        trid = cur.fetchone()
        ukaz = ('INSERT INTO denar_transakcije(id,znesek,uporabnik) VALUES ((%s), (%s), (%s))')
        cur.execute(ukaz, (trid[0], -kolicina, stanje, ))
        redirect ('{0}uporabnik/{1}/'.format(ROOT,stanje))


def vredost_delnic(st):
    ukaz = ("SELECT oznaka, sum(kolicina) FROM delnice_transakcije WHERE uporabnik = (%s) GROUP BY oznaka")
    vrednost = 0
    cur.execute(ukaz, (st, ))
    delnice = cur.fetchall()
    for oznaka, kolicina in delnice:
        ukaz = ("SELECT cena FROM DELNICE where oznaka = (%s)")
        cur.execute(ukaz,(oznaka, ))
        cena  = cur.fetchone()
        vrednost += cena[0]*kolicina
    return vrednost

@get('/uporabnik/<stanje>/trgovanje/')
def pregled_delnic(stanje):
    piskotek = id_uporabnik()

    if piskotek != int(stanje):
        redirect('{0}zacetna_stran/'.format(ROOT))

    ukaz = ("SELECT oznaka, sum(kolicina) FROM delnice_transakcije WHERE uporabnik = (%s) GROUP BY oznaka")
    cur.execute(ukaz, (stanje, ))
    delnice = cur.fetchall()
    vrednost_portfelja = vredost_delnic(stanje)
    cur.execute("SELECT * FROM DELNICE ORDER BY oznaka ASC")
    return rtemplate('delnice.html', stanje = stanje, delnice = delnice, vrednost_portfelja = vrednost_portfelja, vse = cur)



def nova_cena_nakup(kolicina_nakupa, kolicina_vseh):
    if kolicina_nakupa > 0 and kolicina_vseh > 0:
        alfa = round(random.uniform(0.5,2),2)
        novi = 1+alfa*(kolicina_nakupa/kolicina_vseh)
        return novi

def nova_cena_prodaja(kolicina_prodaje, kolicina_vseh):
    if kolicina_prodaje > 0 and kolicina_vseh > 0:
        alfa = round(random.uniform(0.5,2),2)
        novi = 1-alfa*(kolicina_prodaje/kolicina_vseh)
        return novi



@get('/uporabnik/<stanje>/trgovanje/<oznaka>/')
def trgovanje(stanje, oznaka):
    piskotek = id_uporabnik()
    if piskotek != int(stanje):
        redirect('{0}zacetna_stran/'.format(ROOT))
    ukaz =("SELECT cena,kolicina,ime FROM DELNICE where oznaka = (%s)")
    cur.execute(ukaz,(oznaka, ))
    podatek = cur.fetchone()
    cena = podatek[0]
    kolicina_na_voljo = podatek[1]
    ime = podatek[2]
    stevilo_delnic = int(round(kolicina_na_voljo/100,0))
    ukaz = ("SELECT sum(kolicina) FROM delnice_transakcije WHERE uporabnik = (%s) and oznaka = (%s)")
    try:
        cur.execute(ukaz,(stanje, oznaka ))
        podatek = cur.fetchone()
        lastna_kolicina = podatek[0]
        if lastna_kolicina == None:
            lastna_kolicina = 0
        
    except:
        lastna_kolicina = 0
    return rtemplate('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 0, stevilo_delnic = stevilo_delnic)

     

@post('/uporabnik/<stanje>/trgovanje/<oznaka>/')
def trg(stanje, oznaka):
    stanje_na_racunu = stanje_racun(stanje)
    ukaz =("SELECT cena,kolicina,ime FROM DELNICE where oznaka = (%s)")
    cur.execute(ukaz,(oznaka, ))
    podatek = cur.fetchone()
    cena = podatek[0]
    kolicina_na_voljo = podatek[1]
    ime = podatek[2]
    stevilo_delnic = int(round(kolicina_na_voljo/100,0))
    ukaz = ("SELECT sum(kolicina) FROM delnice_transakcije WHERE uporabnik = (%s) AND oznaka = (%s) GROUP BY oznaka")


    try:
        cur.execute(ukaz,(stanje, oznaka))
        podatek = cur.fetchone()
        lastna_kolicina = podatek[0]
    except:
        lastna_kolicina = 0
    try:
        kolicina = int(request.forms.kolicina)
        geslo = request.forms.geslo
        vrsta = request.forms.vrsta
    except:
        return rtemplate('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1, stevilo_delnic = stevilo_delnic)
    if kolicina <= 0:
        return rtemplate('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1, stevilo_delnic = stevilo_delnic)

    if not preveri_geslo(stanje,geslo):
        return rtemplate('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 2, stevilo_delnic = stevilo_delnic)

    if vrsta == 'nakup':
        if kolicina > stevilo_delnic:
            return rtemplate('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1, stevilo_delnic=stevilo_delnic)
        if cena*kolicina > stanje_na_racunu:
            return rtemplate('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1, stevilo_delnic=stevilo_delnic)
        cur.execute("SELECT nextval('trans_id')")
        trid = cur.fetchone()

        ukaz = ('INSERT INTO denar_transakcije(id,znesek,uporabnik) VALUES ((%s), (%s), (%s))')
        cur.execute(ukaz,(trid[0], float(-kolicina*cena), stanje, ))

        ukaz = ('INSERT INTO delnice_transakcije(id,uporabnik,oznaka,kolicina) values((%s),(%s),(%s),(%s))')
        cur.execute(ukaz,(trid[0], stanje, oznaka, kolicina))

        ukaz = ('UPDATE delnice SET kolicina = (%s) WHERE oznaka = (%s)')
        sprememba = kolicina_na_voljo - kolicina
        cur.execute(ukaz,(sprememba, oznaka, ))

        ukaz = ('UPDATE delnice SET cena = (%s) WHERE oznaka = (%s)')
        nova_cena = round(float(cena) * float(nova_cena_nakup(kolicina,kolicina_na_voljo)),2)
        cur.execute(ukaz,(nova_cena, oznaka, ))

        string = '{0}uporabnik/{1}/'.format(ROOT,stanje)
        redirect(string)

    if vrsta =='prodaja':
        if kolicina > lastna_kolicina:
            return rtemplate('operacija.html', stanje = stanje, cena = cena, kolicina1 = kolicina_na_voljo, kolicina2 = lastna_kolicina, ime = ime, oznaka = oznaka, napaka = 1, stevilo_delnic=stevilo_delnic)
        cur.execute("SELECT nextval('trans_id')")
        trid = cur.fetchone()
        
        ukaz = ('INSERT INTO denar_transakcije(id,znesek,uporabnik) VALUES ((%s), (%s), (%s))')
        cur.execute(ukaz,(trid[0],kolicina*cena,stanje, ))

        ukaz = ('INSERT INTO delnice_transakcije(id,uporabnik,oznaka,kolicina) values((%s),(%s),(%s),(%s))')
        cur.execute(ukaz,(trid[0], stanje, oznaka, -kolicina))

        ukaz = ('UPDATE delnice SET kolicina = (%s) WHERE oznaka = (%s)')
        sprememba = kolicina_na_voljo + kolicina
        cur.execute(ukaz,(sprememba, oznaka, ))

        ukaz = ('UPDATE delnice SET cena = (%s) WHERE oznaka = (%s)')
        nova_cena = round(float(cena) * float(nova_cena_prodaja(kolicina,kolicina_na_voljo)),2)
        cur.execute(ukaz,(nova_cena, oznaka, ))

        string = '{0}uporabnik/{1}/'.format(ROOT,stanje)
        redirect(string)

@post('/posodobi/')
def posodobi():
    if id_uporabnik() != 69:
        redirect('{0}zacetna_stran/'.format(ROOT))
    cur.execute("SELECT oznaka FROM DELNICE")
    oznake = cur.fetchall()
    for oznaka in oznake:
        sprememba = round(random.uniform(0.8,1.2),2)
        cur.execute("SELECT cena FROM DELNICE WHERE oznaka = (%s)", (oznaka[0], ))
        x = cur.fetchone()
        cena = round(float(x[0]) * sprememba,2)
        cur.execute("UPDATE delnice SET cena = (%s) WHERE oznaka = (%s)", (cena, oznaka[0], ))
    redirect('{0}uporabnik/69/'.format(ROOT))



baza = psycopg2.connect(database=db, host=host, user=user, password=password, port = DB_PORT)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)


run(host='localhost', port=SERVER_PORT, reloader=RELOADER)

