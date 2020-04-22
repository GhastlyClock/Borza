from bottle import *
import requests

import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s sumniki


# Mapa za statične vire (slike, css, ...)
static_dir = "./static"

@route("/static/<filename:path>")
def static(filename):
    return static_file(filename, root=static_dir)

@get('/')
def index():
    return template ('zacetna_stran.html')

@get('/zacetna_stran/')
def zacetna_get():
    return template('zacetna_stran.html')

run(host='localhost', port=8080, reoloader=True)

