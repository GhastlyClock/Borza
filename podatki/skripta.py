import requests
import orodja
import  re

zgreseni = 0
zgreseni2 = 0
slovar = []
slovar2 = []
#for i in range(0,80):
#    orodja.pripravi_imenik(f'zajeti_podatki/{i+1}. stran.html')
#    orodja.shrani_spletno_stran(f'https://money.cnn.com/data/markets/russell/?page={i}', f'zajeti_podatki/{i+1}. stran.html')
vzorec = (
    r'<a class="wsod_symbol" href=".*?">(?P<Oznaka>\w{3,4})'
    r'</a>&nbsp;(?P<Ime_podjetja>.+?)</td>'
    r'<td><span stream="last_\d+" streamFeed="MorningstarQuote">'
    r'(?P<Cena>.+?)</span></td><td><span stream="change_\d+" streamFeed="MorningstarQuote"><span class=".*?">'
    r'(?P<Sprememba_cene>.+?)</span></span></td><td><span stream="changePct_\d+" streamFeed="MorningstarQuote"><span class=".*?">'
    r'(?P<Sprememba_v_odstotkih>.+?)</span></span></td><td>'
    r'(?P<PE_razmerje>.+?)</td><td>'
    r'(?P<Stevilo_delnic>.+?)</td><td><span class=".*?">'
    r'(?P<Sprememba_do_danes>.+?)<')





for i in range(0,80):
    with open(f'zajeti_podatki/{i+1}. stran.html', encoding='utf8') as f:
        vsebina = f.read()

    zgreseni = 0
    for zadetek in re.finditer(vzorec,vsebina):
        slovar.append(zadetek.groupdict())
        zgreseni = zgreseni + 1
    
    zgreseni2 = 15 - zgreseni + zgreseni2
print(slovar, zgreseni2)
orodja.zapisi_csv(slovar, slovar[0].keys(),'podatki.csv')