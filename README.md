# NL2SQL

NL2SQL è una piccola applicazione web che traduce domande formulate in italiano in query SQL. Usa un LLM eseguito localmente, così la generazione delle query avviene tramite Ollama e il modello `phi3`.

## Architettura

- **Backend** — `backend/app.py` espone un'API FastAPI. L'endpoint `POST /query` riceve una domanda, recupera lo schema delle tabelle `Customer`, `Invoice`, `InvoiceLine` e `Track` dal database SQLite, incluse le chiavi esterne tra queste tabelle, e lo invia a Ollama con la domanda. Il backend accetta solo query che iniziano con `SELECT`, apre il database in sola lettura e restituisce la query e i risultati in JSON.
- **Frontend** — `frontend/index.html` contiene HTML, CSS e JavaScript. Permette di inviare una domanda al backend e mostra la query generata, i risultati in una tabella o un messaggio di errore.
- **Database** — `backend/Chinook_Sqlite.sqlite` è il database usato dall'applicazione. È necessario per il funzionamento del progetto e non viene escluso dal `.gitignore`.

## Requisiti

- Python 3 e pip
- [Ollama](https://ollama.com/) installato
- Il modello `phi3` scaricato in Ollama

## Installazione e avvio

### 1. Avvia Ollama

Assicurati che il servizio Ollama sia attivo. Se non è già in esecuzione, avvialo secondo le istruzioni della tua installazione. Scarica il modello richiesto:

```powershell
ollama pull phi3
```

### 2. Installa le dipendenze del backend

Dalla cartella principale del progetto, apri un terminale PowerShell ed esegui:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. Avvia il backend

Nello stesso terminale, sempre dentro `backend`:

```powershell
python -m uvicorn app:app --reload
```

L'API sarà disponibile su `http://127.0.0.1:8000`. Una richiesta GET a `/` restituisce `{"stato":"ok"}`.

### 4. Avvia il frontend

Apri un secondo terminale PowerShell, dalla cartella principale del progetto:

```powershell
cd frontend
python -m http.server 5500 --bind 127.0.0.1
```

Apri quindi `http://127.0.0.1:5500` nel browser. Il backend consente richieste dal frontend servito su `localhost` o `127.0.0.1` tramite CORS. Servire la pagina con il server HTTP locale evita problemi dovuti all'apertura diretta del file.

### 5. Invia una domanda

Scrivi una domanda nella pagina e premi **Invia**. In alternativa, l'endpoint accetta una richiesta come:

```http
POST http://127.0.0.1:8000/query
Content-Type: application/json

{"domanda":"Quanti clienti ci sono?"}
```

La risposta contiene la query SQL generata e un array `risultati` con le righe restituite dal database.

## Limiti noti

- `phi3` può impiegare molto tempo o entrare in un ciclo di generazione davanti a domande complesse; in questi casi è possibile interrompere la richiesta e provare a riformulare la domanda in modo più semplice.
- Il modello può generare SQL non valido o interpretare male una domanda. Il controllo che accetta solo query con prefisso `SELECT` e l'apertura del database in sola lettura limitano le operazioni eseguibili, ma non garantiscono la correttezza dei risultati.
- Nel prompt vengono forniti lo schema e le relazioni delle sole tabelle `Customer`, `Invoice`, `InvoiceLine` e `Track`; le domande che richiedono altre tabelle potrebbero non essere gestite correttamente.
- Non è previsto un limite o una paginazione dei risultati: query che restituiscono molte righe possono richiedere più tempo e produrre risposte voluminose.
- Le prestazioni dipendono dalle risorse del computer e dalla velocità di Ollama, che esegue il modello localmente.
