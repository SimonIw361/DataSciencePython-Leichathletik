import requests # type: ignore
import pandas as pd # type: ignore
import numpy as np # type: ignore
from bs4 import BeautifulSoup # type: ignore

#Quelle zu Funktionen BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/index.html#get-text

def bestenlisteAlleJahre(disziplin, anzahlSeiten):
    """
    return Array mit DataFrame fur einige Jahre (an Stelle 0 ist 2025, an Stelle 5 ist 2020)
    """
    bestenlistenJahre = []
    for i in range(0,6):
        bestenlistenJahre.append(makeKompletteBestenliste(disziplin,str(2025-i),anzahlSeiten))
    return bestenlistenJahre


def makeKompletteBestenliste(disziplin, jahr, anzahlSeiten): #eine seite hat 30 Eintraege
    """
    Funktion 1: von aussen aufrufen, disziplin jahr und anzahl Seiten uebergeben, ruft immer wieder Funktion2 auf (so oft wie Anzahl der Seiten)
    return gibt gesamte Tabelle für ein Jahr mit Daten zurück
    """
    if disziplin != "200" and disziplin != "100": #nur fuer bestimmte Disziplinen und Jahre
       raise ValueError("Disziplin gibt es nicht")
    if int(jahr) > 2025 and int(jahr) < 2020: #jahr muss zwischen 2025 und 2020 sein
        raise ValueError("Jahr gibt es nicht")
    
    url = "https://bestenliste.leichtathletik.de/Performances?performanceList=4ccb20ca-2309-4462-9f18-ef1cf06db244&pageNumber=1&classcode=M&eventcode="+ disziplin + "&environment=1&year="+ jahr +"&showForeigners=1"
    bestenliste = pd.DataFrame(columns=["Platz", "Zeit", "Wind", "Name", "Verein", "Nationalitaet", "Jahrgang", "AK", "Datum", "Ort"])
    for i in range(1,1 + anzahlSeiten):
        urlSplit = url.split("pageNumber=1")
        if len(urlSplit) != 2:
            raise RuntimeError("Suchkriterium pageNumber ist in URL nicht enthalten")
        suchURL = urlSplit[0] + "pageNumber=" + str(i) + urlSplit[1]

        page = requests.get(suchURL)
        soup = BeautifulSoup(page.content, 'html.parser')
        bestenliste= pd.concat([bestenliste, makeDataFrameAusTeilPage(soup)], ignore_index=True)
    
    #Typen fuer Spalten festelegen, damit damit besser gearbeitet werden kann
    bestenliste["Zeit"] = bestenliste["Zeit"].astype(float)
    bestenliste["Wind"] = bestenliste["Wind"].astype(float)
    bestenliste[["Platz", "Jahrgang"]] = bestenliste[["Platz", "Jahrgang"]].astype(int)
    return bestenliste


def makeDataFrameAusTeilPage(soup):
    """
    Funktion 2: erstellt Tabelle fuer eine Seite (30 Einträge), ruft immer Funktion 3 auf (30x)
    return DataFrame mit 30 Eintraegen
    """
    zeilen = []
    allDivsEntry = soup.find_all('div', class_='entryline')
    for i in range(1,31):
        entry = allDivsEntry[i]
        series = makeSerieAusEntryzeile(entry)
        zeilen.append(series)
    df = pd.DataFrame(zeilen, columns=["Platz", "Zeit", "Wind", "Name", "Verein", "Nationalitaet", "Jahrgang", "AK", "Datum", "Ort"])
    return df


def makeSerieAusEntryzeile(entry):
    """
    Funktion 3: bekommt div von class entryList, erstellt daraus eine Tabellenspalte mit Werten
    return gibt Werte fuer einen Eintrag als Series zurueck
    """
    try:
        allFirstline = entry.find_all(class_="firstline")
        allSecondline = entry.find_all(class_="secondline")
        
        platz = allFirstline[0].get_text().strip()
        zeitString = allFirstline[1].get_text().strip() #zwischen Zeit ein . machen, damit diese spater als float konvertiert werden koennen
        zeit = zeitString.replace(",",".")
        windString = allSecondline[0].get_text().strip()
        wind = windString.replace(",",".")
        name = allFirstline[2].get_text().strip()
        verein = allSecondline[1].get_text().strip()
        nationalitaet = allFirstline[3].get_text().strip()
        jahrgang = allSecondline[2].get_text().strip()
        ak = "M"
        col_95 = entry.find(class_="col-95p")
        datum = col_95.find("div").get_text().strip()

        #Ort abfragen:
        linkOrtDe = col_95.find("a")
        if linkOrtDe == None:
            #Ort ist im Ausland, ist direkt im div darin
            ort = col_95.find(class_="secondline").get_text().strip()
        else:
            #Ort in DE, ist innerhalb a Tag
            ort = linkOrtDe.get_text().strip()

        #Datenbereinigung, bei Jahrgang steht evtl noch AK mit drin, auf zwei Spalten korrekt aufteilen
        if len(jahrgang) > 4:
            arr = jahrgang.split("(")
            jahrgang = arr[0].strip()
            ak = arr[1].strip()[:-1]
        
        index = ["Platz", "Zeit", "Wind", "Name", "Verein", "Nationalitaet", "Jahrgang", "AK", "Datum", "Ort"]
        werte= [platz, zeit, wind, name, verein, nationalitaet, jahrgang, ak, datum, ort]
        zeile = pd.Series(werte, index)
        return zeile
    except:
        raise RuntimeError("Fehler beim Webscraping, die Webseite hat nicht die erwartete Struktur")
