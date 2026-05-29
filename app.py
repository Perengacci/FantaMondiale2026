import streamlit as st
import math
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURAZIONE E DATABASE ---
PASSWORD_ADMIN = "Mondiali2026!" 

# Elenco squadre ufficiale con quote aggiornate
DATI_SQUADRE = {
    "Francia": 5.50, "Spagna": 5.50, "Inghilterra": 7.50, "Brasile": 9.00, "Argentina": 9.00,
    "Portogallo": 11.00, "Germania": 14.00, "Paesi Bassi": 21.00, "Belgio": 26.00, "Uruguay": 29.00,
    "Croazia": 31.00, "Norvegia": 31.00, "Colombia": 31.00, "Danimarca": 41.00, "Svizzera": 51.00,
    "Austria": 51.00, "USA": 61.00, "Messico": 61.00, "Marocco": 61.00, "Giappone": 81.00
}

# Inizializzazione della connessione nativa a Google Sheets (legge dai Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

def carica_pronostici():
    try:
        # Legge la scheda 'pronostici', ignorando la cache (ttl=0) per dati sempre freschi
        df = conn.read(worksheet="pronostici", ttl=0)
        # Se il foglio è vuoto o ha solo le intestazioni, restituisce un dizionario vuoto
        if df.empty or len(df) == 0:
            return {}
        # Rimuove righe completamente vuote per sicurezza
        df = df.dropna(subset=["Giocatore"])
        return df.set_index("Giocatore").to_dict(orient="index")
    except Exception as e:
        return {}

def carica_risultati_reali():
    try:
        df = conn.read(worksheet="admin", ttl=0)
        if not df.empty and len(df) > 0:
            return [df.iloc[0]["R1"], df.iloc[0]["R2"], df.iloc[0]["R3"]]
    except:
        pass
    return ["-- Seleziona --", "-- Seleziona --", "-- Seleziona --"]

# --- 2. LOGICA MATEMATICA DEL PUNTEGGIO ---
def calcola_coefficiente(quota):
    if quota < 5:
        return 1.0
    return round(1 + math.sqrt((quota - 5) / 3), 2)

def calcola_punti_scelta(posizione_pronosticata, squadra_scelta, podio_reale):
    if pd.isna(squadra_scelta) or squadra_scelta not in podio_reale or "-- Seleziona --" in podio_reale:
        return 0.0
    
    pos_reale = podio_reale.index(squadra_scelta) + 1
    distanza = abs(posizione_pronosticata - pos_reale)
    
    # Punteggio Base iniziale
    if posizione_pronosticata == 1:
        punti_base = 100
    elif posizione_pronosticata == 2:
        punti_base = 75
    else:
        punti_base = 50
        
    # Applicazione riduzione per distanza (40% se dist=1, 60% se dist=2)
    if distanza == 1:
        punti_base *= 0.60
    elif distanza == 2:
        punti_base *= 0.40
        
    quota = DATI_SQUADRE.get(squadra_scelta, 5.50)
    return round(punti_base * calcola_coefficiente(quota), 2)

# --- 3. INTERFACCIA UTENTE (STREAMLIT) ---
st.set_page_config(page_title="Fanta-Mondiale 2026", layout="centered")
st.title("🏆 Fanta-Mondiale 2026")

# Generazione dinamica dei testi dei menu a tendina con i moltiplicatori visibili
opzioni_formattate = ["-- Seleziona --"]
mapping_scelte = {"-- Seleziona --": "-- Seleziona --"}
for squadra, quota in DATI_SQUADRE.items():
    cd = calcola_coefficiente(quota)
    testo = f"{squadra} (Moltiplicatore: {cd})"
    opzioni_formattate.append(testo)
    mapping_scelte[testo] = squadra

# Navigazione laterale
modalita = st.sidebar.radio("Navigazione", ["📊 Classifica & Quote", "🔮 Inserisci Pronostico", "⚙️ Area Admin"])

# Caricamento centralizzato dei dati dal Cloud di Google
giocatori_salvati = carica_pronostici()
podio_reale_corrente = carica_risultati_reali()

# --- SCHERMATA 1: CLASSIFICA & QUOTE ---
if modalita == "📊 Classifica & Quote":
    tab1, tab2 = st.tabs(["📈 Classifica Generale", "📋 Tabellone Quote"])
    
    with tab1:
        if "-- Seleziona --" in podio_reale_corrente:
            st.info("I risultati reali non sono ancora stati inseriti dall'organizzatore. Sotto vedi i pronostici attuali.")
        
        tabella_classifica = []
        for nome, prono in giocatori_salvati.items():
            p1 = calcola_punti_scelta(1, prono["P1"], podio_reale_corrente)
            p2 = calcola_punti_scelta(2, prono["P2"], podio_reale_corrente)
            p3 = calcola_punti_scelta(3, prono["P3"], podio_reale_corrente)
            totale = round(p1 + p2 + p3, 2)
            
            tabella_classifica.append({
                "Giocatore": nome, "1° Posto": prono["P1"], "2° Posto": prono["P2"], "3° Posto": prono["P3"], "Punti": totale
            })
            
        if tabella_classifica:
            tabella_classifica = sorted(tabella_classifica, key=lambda x: x["Punti"], reverse=True)
            st.table(tabella_classifica)
        else:
            st.write("Nessun giocatore ha ancora inserito un pronostico.")

    with tab2:
        st.subheader("Moltiplicatori Ufficiali delle Squadre")
        elenco_quote = [{"Squadra": sq, "Quota Vincente": qta, "Moltiplicatore (CD)": calcola_coefficiente(qta)} for sq, qta in DATI_SQUADRE.items()]
        st.dataframe(elenco_quote, use_container_width=True)

# --- SCHERMATA 2: INSERIMENTO PRONOSTICO ---
elif modalita == "🔮 Inserisci Pronostico":
    st.subheader("Inserisci la tua giocata bloccata")
    nome_utente = st.text_input("Inserisci il tuo Nome e Cognome (es. Mario Rossi):").strip()
    
    if nome_utente:
        if nome_utente in giocatori_salvati:
            scelte = giocatori_salvati[nome_utente]
            st.warning(f"Hai già salvato il tuo pronostico, {nome_utente}!")
            st.success(f"Il tuo podio blindato è: 1° **{scelte['P1']}** | 2° **{scelte['P2']}** | 3° **{scelte['P3']}**")
            st.caption("Per ragioni di sicurezza e correttezza, non puoi modificare un pronostico esistente.")
        else:
            p1_f = st.selectbox("Chi vincerà il Mondiale? (1°)", opzioni_formattate, key="user_p1")
            p2_f = st.selectbox("Chi arriverà 2°?", opzioni_formattate, key="user_p2")
            p3_f = st.selectbox("Chi arriverà 3°?", opzioni_formattate, key="user_p3")
            
            p1, p2, p3 = mapping_scelte[p1_f], mapping_scelte[p2_f], mapping_scelte[p3_f]
            
            if st.button("Salva Pronostico"):
                if "-- Seleziona --" in [p1, p2, p3]:
                    st.error("Devi completare tutte e tre le posizioni del podio!")
                elif len(set([p1, p2, p3])) < 3:
                    st.error("Non puoi inserire squadre duplicate nello stesso podio!")
                else:
                    # Legge lo storico esistente, appende la nuova riga e carica su Google Sheets
                    try:
                        df_esistente = conn.read(worksheet="pronostici", ttl=0)
                    except:
                        df_esistente = pd.DataFrame(columns=["Giocatore", "P1", "P2", "P3"])
                        
                    nuovo_prono = pd.DataFrame([{"Giocatore": nome_utente, "P1": p1, "P2": p2, "P3": p3}])
                    df_aggiornato = pd.concat([df_esistente, nuovo_prono], ignore_index=True)
                    conn.update(worksheet="pronostici", data=df_aggiornato)
                    
                    st.success("Pronostico salvato con successo su Google Sheets!")
                    st.balloons()
                    st.rerun()

# --- SCHERMATA 3: AREA ADMIN ---
elif modalita == "⚙️ Area Admin":
    st.subheader("Pannello Organizzatore")
    pass_inserita = st.text_input("Password Amministratore:", type="password")
    
    if pass_inserita == PASSWORD_ADMIN:
        st.success("Accesso Consentito.")
        opzioni_admin = ["-- Seleziona --"] + list(DATI_SQUADRE.keys())
        
        idx1 = opzioni_admin.index(podio_reale_corrente[0]) if podio_reale_corrente[0] in opzioni_admin else 0
        idx2 = opzioni_admin.index(podio_reale_corrente[1]) if podio_reale_corrente[1] in opzioni_admin else 0
        idx3 = opzioni_admin.index(podio_reale_corrente[2]) if podio_reale_corrente[2] in opzioni_admin else 0
        
        adm_1 = st.selectbox("1° Reale", opzioni_admin, index=idx1)
        adm_2 = st.selectbox("2° Reale", opzioni_admin, index=idx2)
        adm_3 = st.selectbox("3° Reale", opzioni_admin, index=idx3)
        
        if st.button("Aggiorna Classifiche Ufficiali"):
            if len(set([adm_1, adm_2, adm_3])) < 3 and adm_1 != "-- Seleziona --":
                st.error("Il podio reale non può contenere squadre duplicate!")
            else:
                df_admin = pd.DataFrame([{"R1": adm_1, "R2": adm_2, "R3": adm_3}])
                conn.update(worksheet="admin", data=df_admin)
                st.success("Risultati reali aggiornati su Google Sheets! Classifiche ricalcolate.")
                st.rerun()
    elif pass_inserita != "":
        st.error("Password errata.")
