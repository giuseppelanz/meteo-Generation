# App Meteo OpenMeteo (Python)

Questa è una nuova app web che usa OpenMeteo per ricavare il meteo attuale di una città con previsione a 5 giorni.

## 🔒 Sicurezza e Dati Sensibili

Questa app è **completamente sicura da mostrare al mondo** perché:

### ✅ Protezione dei Dati Sensibili
- **File `.env`**: Tutte le configurazioni sensibili (API URLs, secret keys, porte) sono gestite tramite variabili d'ambiente nel file `.env`
- **File `.env` escluso da Git**: Il file `.env` non viene mai inviato a repository pubblici (vedi `.gitignore`)
- **Template `.env.example`**: Fornisce un template sicuro per chi clona il progetto
- **Nessuna API key hardcoded**: Non ci sono credenziali nel codice sorgente

### ✅ Privacy Utente
- **Nessun tracciamento**: L'app non raccoglie né trasmette dati personali
- **Nessuna API key richiesta**: Utilizza OpenMeteo API gratuita senza autenticazione
- **Dati locali**: Tutte le ricerche rimangono sul tuo server/computer
- **Open source**: Tutto il codice è disponibile per la revisione

### 📋 Checklist antes di pubblicare:
1. ✅ `.env` file **non sincronizzato** su GitHub
2. ✅ `.env` aggiunto a `.gitignore`
3. ✅ Utilizza `.env.example` come template pubblico
4. ✅ Nessuna credenziale nel codice sorgente

## 🎯 Ricerca Città Intelligente

L'app ha un **algoritmo intelligente di selezione città** che:
- **Evita duplicati**: Se cerchi "Venezia", ottieni direttamente Venezia (città), non 10 risultati casuali
- **Predilige città capoluogo**: Seleziona le città principali piuttosto che comuni minori
- **Offre scelta per omonime distanti**: Se cerchi una città con diverse omonime in paesi diversi e distanti (>500km), l'app ti chiede quale selezionare

**Esempi:**
- Cerchi "Roma" → vedi direttamente Roma, Italia (non "Roma" per provincia, comune, etc.)
- Cerchi "Springfield" → scegli tra Springfield USA e Springfield Regno Unito (a >500km di distanza)

## Funzionalità

-  Scrivi il nome della città (accetta spazi e maiuscole/minuscole in qualsiasi forma)
-  Gestione errori input non valido (alfanumerico/nessuna città valida)
-  Ricerca tramite OpenMeteo Geocoding API con filtro intelligente
-  Scelta della città se ci sono più match distanti (es. città omonime in paesi diversi)
-  Visualizza il meteo corrente: temperatura, vento, direzione vento, umidità
-  Mostra previsione meteo 5 giorni: temperature min/max, precipitazioni, velocità massima del vento

## Avvio

### Avvio veloce (Windows) - CONSIGLIATO ✨

Semplicemente **doppio-click** su `launch.bat` nella cartella. Questo script:
- Crea automaticamente il virtual environment se non esiste
- Installa le dipendenze
- Avvia il server
- **Apre automaticamente il browser alla pagina web**

Poi la pagina si aprirà automaticamente su:
**http://127.0.0.1:5000/**

---

### Avvio manuale (Windows PowerShell)
cd "<path/to/your/app>"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Poi apri nel browser:
**http://127.0.0.1:5000/**

### Opzione 2: Mac/Linux

```bash
cd "<path/to/your/app>"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Poi apri nel browser:
**http://127.0.0.1:5000/**

## Link rapido

Una volta che il server è in esecuzione, clicca qui:

- [🌍 Apri l'interfaccia web](http://127.0.0.1:5000/)

## Design e UX

- **Interfaccia moderna**: Utilizza Bootstrap 5 con effetti glassmorphism
- **Sfondo dinamico**: Il colore di sfondo cambia automaticamente in base alle condizioni meteo attuali:
  - ☀️ Soleggiato: Gradiente caldo giallo-arancione
  - ☁️ Nuvoloso: Gradiente grigio-blu
  - 🌧️ Pioggia: Gradiente blu scuro
  - ❄️ Neve: Gradiente bianco-ghiaccio
  - ⛈️ Temporale: Gradiente scuro
  - 🌫️ Nebbia: Gradiente grigio
- **Icone meteo**: Emoji grandi per rappresentare visivamente il tempo
- **Responsive**: Funziona su desktop e mobile

## Sicurezza

L'app è progettata per l'uso locale e non condivide informazioni sensibili:
- **Nessuna chiave API richiesta**: Utilizza OpenMeteo API gratuita senza autenticazione
- **Dati locali**: Tutti i dati rimangono sul tuo computer
- **Secret key sicura**: Configurata per lo sviluppo locale
- **Connessioni sicure**: Utilizza HTTPS per le API esterne quando disponibile

**Nota**: Questa app è per uso personale locale. Non esporla su internet pubblico senza ulteriori configurazioni di sicurezza.

## Troubleshooting

**Problema:** Il link nel README non si apre o dà errore di connessione

**Soluzione:**
1. Assicurati di aver avviato il server con `python app.py`
2. Vedrai output simile a: `* Running on http://127.0.0.1:5000`
3. Apri il browser e digita manualmente: **http://127.0.0.1:5000/**
4. Se ancora non funziona, controlla che la porta 5000 non sia in uso da un'altra app

**Problema:** Errore "Modulo non trovato" quando avvio `python app.py`

**Soluzione:**
1. Verifica di aver installato le dipendenze: `pip install -r requirements.txt`
2. Verifica di essere nel virtual environment corretto (venv attivo)
3. Se usi Python 3.14+, potrebbe essere un problema di compatibilità - aggiorna Flask e requests: `pip install --upgrade Flask requests`


