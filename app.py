import streamlit as st
import math
import json
import os

# --- 1. CONFIGURAZIONE E DATABASE ---
PASSWORD_ADMIN = "Mondiali2026!" 

DATI_SQUADRE = {
    "Francia": 5.50, "Spagna": 5.50, "Inghilterra": 7.50, "Brasile": 9.00, "Argentina": 9.00,
    "Portogallo": 11.00, "Germania": 14.00, "Paesi Bassi": 21.00, "Belgio": 26.00, "Uruguay": 29.00,
    "Croazia": 31.00, "Norvegia": 31.00, "Colombia": 31.00, "Danimarca": 41.00, "Svizzera": 51.00,
    "Austria": 51.00, "USA": 61.00, "Messico": 61.00, "Marocco": 61.00, "Giappone": 81.00
}

FILE_LOCAL_DB = "database_fanta.json"

def carica_tutto():
    if not os.path.exists(FILE_LOCAL_DB):
        return {"risultati_reali": ["-- Seleziona --", "-- Seleziona --", "-- Seleziona --"], "giocatori": {}}
    try:
        with open(FILE_LOCAL_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"risultati_reali": ["-- Seleziona --", "-- Seleziona --", "-- Seleziona --"], "giocatori": {}}

def salva_tutto(dati):
    with open(FILE_LOCAL_DB, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

# Carichiamo i dati all'avvio
if "dati_gioco" not in st.session_state:
    st.session_state.dati_gioco = carica_tutto()

# --- 2. LOGICA MATEMATICA ---
def calcola_coefficiente(quota):
    if quota < 5:
        return 1.0
    return round(1 + math.sqrt((quota - 5) / 3), 2)

def calcola_punti_scelta(posizione_pronosticata, squadra_scelta, podio_reale):
    if not squadra_scelta or squadra_scelta not in podio_reale or "-- Seleziona --" in podio_reale:
        return 0.0
    
    pos_reale = podio_reale.index(squadra_scelta) + 1
    distanza = abs(posizione_pronosticata - pos_reale)
    
    if posizione_pronosticata == 1:
        punti_base = 100
    elif posizione_pronosticata == 2:
        punti_base = 75
    else:
        punti_base = 50
        
    if distanza == 1:
        punti_base *= 0.60
    elif distanza == 2:
        punti_base *= 0.40
        
    quota = DATI_SQUADRE.get(squadra_scelta, 5.50)
    return round(punti_base * calcola_coefficiente(quota), 2)

# --- 3. INTERFACCIA UTENTE ---
st.set_page_config(page_title="Fanta-Mondiale 2026", layout="centered")
st.title("🏆 Fanta-Mondiale 2026")

opzioni_formattate = ["-- Seleziona --"]
mapping_scelte = {"-- Seleziona --": "-- Seleziona --"}
for squadra, quota in DATI_SQUADRE.items():
    cd = calcola_coefficiente(quota)
    testo = f"{squadra} (Moltiplicatore: {cd})"
    opzioni_formattate.append(testo)
    mapping_scelte[testo] = squadra

modalita = st.sidebar.radio("Navigazione", ["📊 Classifica & Quote", "🔮 Inserisci Pronostico", "⚙️ Area Admin"])

giocatori_salvati = st.session_state.dati_gioco["giocatori"]
podio_reale_corrente = st.session_state.dati_gioco["risultati_reali"]

# --- SCHERMATA 1: CLASSIFICA ---
if modalita == "📊 Classifica & Quote":
    tab1, tab2 = st.tabs(["📈 Classifica Generale", "📋 Tabellone Quote"])
    
    with tab1:
        if "-- Seleziona --" in podio_reale_corrente:
            st.info("I risultati reali non sono ancora stati inseriti. Sotto vedi i pronostici attuali.")
        
        tabella_classifica = []
        for nome, prono in giocatori_salvati.items():
            p1 = calcola_punti_scelta(1, prono[0], podio_reale_corrente)
            p2 = calcola_punti_scelta(2, prono[1], podio_reale_corrente)
            p3 = calcola_punti_scelta(3, prono[2], podio_reale_corrente)
            totale = round(p1 + p2 + p3, 2)
            
            tabella_classifica.append({
                "Giocatore": nome, "1° Posto": prono[0], "2° Posto": prono[1], "3° Posto": prono[2], "Punti": totale
            })
            
        if tabella_classifica:
            tabella_classifica = sorted(tabella_classifica, key=lambda x: x["Punti"], reverse=True)
            st.table(tabella_classifica)
        else:
            st.write("Nessun giocatore ha ancora inserito un pronostico.")

    with tab2:
        elenco_quote = [{"Squadra": sq, "Quota Vincente": qta, "Moltiplicatore (CD)": calcola_coefficiente(qta)} for sq, qta in DATI_SQUADRE.items()]
        st.dataframe(elenco_quote, use_container_width=True)

# --- SCHERMATA 2: INSERIMENTO PRONOSTICO ---
elif modalita == "🔮 Inserisci Pronostico":
    st.subheader("Inserisci la tua giocata bloccata")
    nome_utente = st.text_input("Inserisci il tuo Nome e Cognome:").strip()
    
    if nome_utente:
        if nome_utente in giocatori_salvati:
            scelte = giocatori_salvati[nome_utente]
            st.warning(f"Hai già salvato il tuo pronostico, {nome_utente}!")
            st.success(f"Il tuo podio blindato è: 1° **{scelte[0]}** | 2° **{scelte[1]}** | 3° **{scelte[2]}**")
        else:
            p1_f = st.selectbox("Chi vincerà il Mondiale? (1°)", opzioni_formattate, key="user_p1")
            p2_f = st.selectbox("Chi arriverà 2°?", opzioni_formattate, key="user_p2")
            p3_f = st.selectbox("Chi arriverà 3°?", opzioni_formattate, key="user_p3")
            
            p1, p2, p3 = mapping_scelte[p1_f], mapping_scelte[p2_f], mapping_scelte[p3_f]
            
            if st.button("Salva Pronostico"):
                if "-- Seleziona --" in [p1, p2, p3]:
                    st.error("Devi completare tutto il podio!")
                elif len(set([p1, p2, p3])) < 3:
                    st.error("Non puoi inserire squadre duplicate!")
                else:
                    # Salviamo nello stato interno ed emaniamo il salvataggio su file
                    st.session_state.dati_gioco["giocatori"][nome_utente] = [p1, p2, p3]
                    salva_tutto(st.session_state.dati_gioco)
                    st.success("Pronostico blindato con successo!")
                    st.balloons()
                    st.rerun()

# --- SCHERMATA 3: AREA ADMIN ---
elif modalita == "⚙️ Area Admin":
    st.subheader("Pannello Organizzatore")
    pass_inserita = st.text_input("Password:", type="password")
    
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
                st.session_state.dati_gioco["risultati_reali"] = [adm_1, adm_2, adm_3]
                salva_tutto(st.session_state.dati_gioco)
                st.success("Risultati reali aggiornati!")
                st.rerun()
                
        # TRUCCO DI BACKUP: Mostra il codice JSON da copiare in caso di emergenza server
        st.divider()
        st.subheader("📦 Backup Codice Dati")
        st.caption("Se il server si riavvia, puoi incollare questo codice nei segreti per non perdere nulla:")
        st.code(json.dumps(st.session_state.dati_gioco, indent=2))
    elif pass_inserita != "":
        st.error("Password errata.")
