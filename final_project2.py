import mysql.connector
from contextlib import contextmanager
from datetime import datetime

@contextmanager
def connect_to_database():
    #Připojení k databázi, fce poskytuje spojeni dalším fcím v programu
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="7364",  
            database="task_manager" 
        )
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ukoly ( id INT AUTO_INCREMENT PRIMARY KEY, 
                                nazev varchar (50) not null, popis varchar (80) not null, 
                                stav enum ('nezahájeno', 'probíhá', 'hotovo' ) default 'nezahájeno', 
                                datum datetime DEFAULT CURRENT_TIMESTAMP)
                        """)
        conn.commit()

        yield conn, cursor
    except mysql.connector.Error as e:
        print(f"Chyba při připojení: {e}")
        return None
    finally:
        cursor.close ()
        conn.close ()


def pridat_ukol ():
#1 fce umoznuje pridat ukoly do tabulky, nazev i popis je povinny    
    with connect_to_database() as (conn, cursor):
        if conn:
            nazev_ukolu = input(f"Zadejte název úkolu: ")
            while len(nazev_ukolu) == 0:
            #smycka bezi dokud nedostane platny vstup
                nazev_ukolu = input(f"Zadejte název úkolu: ")
            popis_ukolu = input (f"Zadejte popis úkolu: ")
            while len(popis_ukolu) == 0:
            #smycka bezi dokud nedostane platny vstup
                popis_ukolu = input (f"Zadejte popis úkolu: ")   
            # zabezpečení inputu placeholdery
            query = "INSERT INTO ukoly (nazev, popis) VALUES (%s, %s);"
            values = (nazev_ukolu,popis_ukolu)
            cursor.execute(query,values)
            conn.commit()
            print (f"Úkol {nazev_ukolu} byl vložen")


def zobrazit_ukoly ():
#2 umoznuje zobrazit ukoly, pokud nejake jsou rozpracované, pokud ne, vraci upozorneni
    with connect_to_database() as (conn, cursor):
        if conn:
            cursor.execute ("SELECT * FROM ukoly where stav = 'nezahájeno' or stav = 'probíhá'" )
            seznam = cursor.fetchall()
            if seznam:
                print ("zobrazuji seznam ukolu")
                for radek in seznam:
                    id = radek [0]
                    nazev = radek [1]
                    popis = radek [2]
                    stav = radek [3]
                    datum = radek [4]
                    datum = datum.strftime("%d.%m.%Y")
                    print(f"ID: {id}, Název úkolu: {nazev}, Popis úkolu: {popis}, Stav: {stav}, Datum: {datum}")
            else:
                print("Seznam je prázdný.")
            
def aktualizovat_ukoly ():
    #3 moznost zmenit stav ukolu, kontroluje, jestli seznam existuje, pak vypise ukoly
    with connect_to_database() as (conn, cursor):
        if conn:
            cursor.execute ("SELECT * FROM ukoly" )
            seznam = cursor.fetchall()
            if seznam:
                print ("zobrazuji seznam ukolu")
                for radek in seznam:
                    id = radek [0]
                    nazev = radek [1]
                    stav = radek [3]
                    print(f"ID: {id}, Název úkolu: {nazev}, Stav: {stav},")
            else:
                print("Seznam je prázdný.")
                return
        while True:    
            vybrane_id = input("Vyberte úkol k aktualizaci podle ID: ")
            try:
                vybrane_id = int(vybrane_id)
                if (vybrane_id <= 0) or (vybrane_id > len(seznam)):
                    print("Vyberte ID ze seznamu! ")
                else:
                    break
            except ValueError:
                print("Pouze čísla!vyber číslo ID ze seznamu: ")
        novy_stav = input("Zvolte nový stav úkolu: 'probíhá'/'hotovo' ")
        while novy_stav not in ("probíhá" , "hotovo"):
            novy_stav = input ("Čti pořádně! Vyber stav z daných možností: ")
        # uprava stavu ukolu podle ID, stav musí být z definovaných hodnot               
        query = ("UPDATE ukoly SET stav = %s WHERE id = %s" )
        values = (novy_stav, vybrane_id)
        cursor.execute (query,values)
        conn.commit()
        print("Úkol byl aktualizován")
        
def odstranit_ukol():
    #4 odstrani ukol trvale z tabulky, kontroluje jestli zadane id existuje v seznamu
    with connect_to_database() as (conn, cursor):
        if conn:
            cursor.execute ("SELECT * FROM ukoly" )
            seznam = cursor.fetchall() 
            if seznam:
                print ("zobrazuji seznam ukolu")
                for radek in seznam:
                    id = radek [0]
                    nazev = radek [1]
                    stav = radek [3]
                    print(f"ID: {id}, Název úkolu: {nazev}, Stav: {stav},")
            else:
                print("Seznam je prázdný.")
                return
        while True:    
            vybrane_id = input("Vyberte úkol ke smazání podle ID: ")
            try:
                vybrane_id = int(vybrane_id)
                if (vybrane_id <= 0) or (vybrane_id > len(seznam)):
                    print("Vyberte ID ze seznamu! ")
                else:
                    break
            except ValueError:
                print("Pouze čísla!vyber číslo ID ze seznamu: ") 
        
        query = ("DELETE FROM ukoly WHERE id = %s")
        values = (vybrane_id,)
        cursor.execute (query,values)
        conn.commit()
        print("Úkol byl smazán.")
        

def hlavni_menu ():
#fce bezi dokud neni ukoncena, platne vstupy postupuji do dalsich funkci, neplatne vraci dotaz na opravu vstupu        
    while True:
        print ("\nSprávce úkolů - hlavní menu:\n 1. Přidat nový úkol\n 2. Zobrazit všechny úkoly\n 3. Aktualizovat úkoly \n 4. Odstranit úkol \n 5. Konec programu")
        volba = input("\nVyberte možnost 1. - 5.: \n")
        try:
            volba = int(volba)
            if volba == 1:
                pridat_ukol ()
            elif volba == 2:
                zobrazit_ukoly ()
            elif volba == 3:
                aktualizovat_ukoly ()    
            elif volba == 4:
                odstranit_ukol ()
            elif volba == 5:
                print ("Konec programu.")
                return                    
            elif (0 >= volba) or (volba > 5):
                print ("\nVyberte si možnost z menu. ")
        except ValueError:
            print ("\nMusíte zadat číslo! ")
                

hlavni_menu ()