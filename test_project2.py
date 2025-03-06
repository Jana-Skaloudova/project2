import pytest
import mysql.connector

@pytest.fixture(scope="function")
def dtb_pripojeni():
    # Připojení k dtb, vytvoření testovací tabulky
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="7364",
            database="task_manager"
        )
        if conn.is_connected():
            print ("Připojeno k databázi.")
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_ukoly ( id INT AUTO_INCREMENT PRIMARY KEY, 
                                nazev varchar (50) not null, popis varchar (80) not null, 
                                stav enum ('nezahájeno', 'probíhá', 'hotovo' ) default 'nezahájeno', 
                                datum datetime DEFAULT CURRENT_TIMESTAMP)
                        """)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Chyba při připojení: {e}")
        return None
    # Předání připojení a cursoru
    yield conn, cursor
    # smazání tabulky
    cursor.execute("DROP TABLE IF EXISTS test_ukoly")
    conn.commit()
    # uzavření cursoru a připojení
    try:
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"Chyba při zavírání dtb: {e}")

@pytest.mark.parametrize(
    "nazev, popis",
    [('obycejny ukol','obycejny popis'),
    ('Úkol s velkým Ú','Popis s háčky'),
    ('uk0l.se.$pec_Znaky','nejaky_spe$l?popis')
    ]
    )
def test_pridat_ukol_positive_parametrized(dtb_pripojeni, nazev, popis):
    conn, cursor = dtb_pripojeni
    # Vložení platného záznamu, zkouška omezení znaků
    cursor.executemany("INSERT INTO test_ukoly (nazev, popis) VALUES (%s,%s)", [(nazev,popis)])
    conn.commit()
    # Ověření vložení
    cursor.execute("SELECT * FROM test_ukoly")
    result = cursor.fetchall()
    assert result is not None, "Žádný úkol nebyl vložen."
    for r in result:      
        assert r[1] == nazev, "Název úkolu není správný."
        assert r[2] == popis, "Popis úkolu není správný."
        assert r[3] == "nezahájeno", "Špatný výchozí stav."

@pytest.mark.parametrize(
    "nazev, popis, expected_error",
    [(None,'popis1',r'.*null.*'),
    ('ukol2',None, r'.*null.*'),
    ('dlouhýý úkol'*50,'popis3','Data too long for column'),
    ('ukol4','dlouhýý popis'*80, 'Data too long for column')
    ]
    )
def test_pridat_ukol_negative_parametrized(dtb_pripojeni, nazev, popis, expected_error):
    conn, cursor = dtb_pripojeni
    # Vložení neplatného záznamu, zakázáno NULL v obou sloupcích, omezena délka
    with pytest.raises(mysql.connector.Error, match= expected_error ):
        cursor.executemany(("INSERT INTO test_ukoly (nazev, popis) VALUES (%s, %s)"),[(nazev,popis)]) 
        conn.commit ()


@pytest.mark.parametrize(
    "stav",
    [('probíhá'),
    ('hotovo'),
    ]
    )
def test_aktualizovat_stav_positive_parametrized(dtb_pripojeni, stav):
    conn, cursor = dtb_pripojeni
    # vložení záznamu do prázdné tabulky
    cursor.execute("INSERT INTO test_ukoly (nazev, popis) VALUES ('test_úkol', 'test_popis')")
    conn.commit()
    # update stavu na povolenou hodnotu, default nezahájeno
    for s in stav:
        cursor.execute("UPDATE test_ukoly SET stav = %s WHERE nazev = 'test_úkol'",[stav])
        conn.commit()
        # Ověření updatu
        cursor.execute("SELECT stav FROM test_ukoly WHERE nazev = 'test_úkol'")
        result = cursor.fetchone()
        assert result[0] == stav, "Stav nebyl aktualizován."

def test_aktualizovat_stav_None(dtb_pripojeni):
    conn, cursor = dtb_pripojeni
    # vložení záznamu do prázdné tabulky
    cursor.execute("INSERT INTO test_ukoly (nazev, popis) VALUES ('test_úkol', 'test_popis')")
    conn.commit()
    # update stavu na povolenou hodnotu, NULL není podle zadání zakázáno, je jen default hodnota, mělo by se zakázat?
    cursor.execute("UPDATE test_ukoly SET stav = NULL WHERE nazev = 'test_úkol'")
    conn.commit()
    # Ověření updatu
    cursor.execute("SELECT stav FROM test_ukoly WHERE nazev = 'test_úkol'")
    result = cursor.fetchone()
    assert result[0] == None, "Stav nebyl aktualizován."

def test_aktualizovat_stav_negative(dtb_pripojeni):
    conn, cursor = dtb_pripojeni
    # vložení záznamu do prázdné tabulky
    cursor.execute("INSERT INTO test_ukoly (nazev, popis) VALUES ('test_úkol', 'test_popis')")
    conn.commit()
    # vložení neplatné hodnoty stavu, která není v ENUM definována
    with pytest.raises(mysql.connector.Error, match=r".*truncated.*"):
        cursor.execute("UPDATE test_ukoly SET stav = 'nehotovo' WHERE nazev = 'test_úkol'")

     
def test_smazat_ukol_positive(dtb_pripojeni):
    conn, cursor = dtb_pripojeni
    # vložení více záznamů do prázdné tabulky   
    values = [("ukol1","popis1"),
            ("ukol2","popis2")] 
    cursor.executemany("INSERT INTO test_ukoly (nazev, popis) VALUES (%s, %s)", values)
    conn.commit() 
    # odstranění existujícího úkolu podle shody popisu
    cursor.execute ("DELETE FROM test_ukoly WHERE nazev = 'ukol1'")
    conn.commit ()
    # ověření, že byl smazán správný úkol
    cursor.execute("SELECT * FROM test_ukoly WHERE nazev = 'ukol1'")
    result = cursor.fetchone()
    assert result is None, "Úkol nebyl smazán."
    cursor.execute("SELECT * FROM test_ukoly")
    result = cursor.fetchall()
    assert result is not None, "Byly smazány všechny úkoly!"

def test_smazat_ukol_negative(dtb_pripojeni):
    conn, cursor = dtb_pripojeni
    # vložení více záznamů do prázdné tabulky    
    values = [("ukol1","popis1"),
            ("ukol2","popis2"),
            ("ukol3","popis3")] 
    cursor.executemany("INSERT INTO test_ukoly (nazev, popis) VALUES (%s, %s)", values)
    conn.commit() 
    # spočítání záznamů v tabulce
    cursor.execute ("SELECT COUNT(*) FROM test_ukoly")
    pocatecni_pocet = cursor.fetchone () [0]
    # mazání neexistujícího úkolu
    cursor.execute ("DELETE FROM test_ukoly WHERE nazev = 'neexistujici_nazev'")
    conn.commit ()
    # spočítání záznamů v tabulce
    cursor.execute ("SELECT COUNT(*) FROM test_ukoly")
    finalni_pocet = cursor.fetchone () [0]
    # porovnaní počtu před a po mazání
    assert pocatecni_pocet == finalni_pocet, "Finální počet záznamů neodpovídá."
    
