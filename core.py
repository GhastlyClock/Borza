from bottle import *
import requests
from auth_public import *

import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki

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

@route("/static/<filename:path>")
def static(filename):
    return static_file(filename, root=static_dir)

@get('/')
def index():
    return template('zacetna_stran.html')

@get('/zacetna_stran/')
def zacetna_get():
    return template('zacetna_stran.html')

@get('/borze/')
def borze():
    cur.execute("SELECT * FROM BORZE")
    return template('borze.html', borze=cur)

@get('/borze/<oznaka>')
def borza(oznaka):
    ukaz = ("SELECT (oznaka,ime,cena,sektor,kolicina) FROM DELNICE WHERE borza = (%s)")
    cur.execute(ukaz,(oznaka, ))
    return template('borze_podrobno.html', delnice=cur, oznaka=oznaka)

baza = psycopg2.connect(database=db, host=host, user=user, password=password)
baza.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
cur = baza.cursor(cursor_factory=psycopg2.extras.DictCursor)

run(host='localhost', port=8080, reoloader=True)

