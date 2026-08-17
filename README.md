# AskyVet

Piattaforma di divulgazione veterinaria: un blog con sezione forum.

- **Blog** — gli amministratori pubblicano articoli con copertina, categoria e tag.
- **Forum** — gli utenti aprono topic liberi (stile Reddit) oppure collegati a un
  articolo, con post, risposte a un livello e like.
- **Moderazione** — gli amministratori creano altri amministratori, cancellano
  contenuti, bannano utenti e li silenziano a tempo.

## Struttura

```
AskyVet/
├── backend/              # API Django + DRF
│   ├── config/           # settings, urls, paginazione
│   ├── common/           # utility condivise fra le app
│   ├── users/            # utenti, autenticazione, moderazione
│   ├── articles/         # blog
│   ├── forum/            # topic, post, risposte, like
│   ├── requirements/     # base.txt (runtime) + dev.txt (tooling)
│   └── manage.py
├── frontend/             # applicazione React (Vite + TypeScript + Tailwind)
│   └── src/              # lib/ components/ pages/ — vedi frontend/README.md
├── docker-compose.yml
└── .env.example
```

## Avvio

### Con Docker

```bash
cp .env.example .env          # e completa i valori
docker compose up --build
```

### In locale

Serve un PostgreSQL in ascolto (`docker compose up db` basta).

```bash
cp .env.example .env
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements/dev.txt

cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Documentazione interattiva su http://localhost:8000/api/swagger/.

### Frontend

In un secondo terminale, con il backend già avviato:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev                   # http://localhost:5173
```

Dettagli e struttura in [frontend/README.md](frontend/README.md).

## Test

Girano su SQLite in memoria, quindi non serve un database attivo.

```bash
cd backend
python manage.py test --settings=config.settings_test
```

## API

Base URL: `/api`. Le liste sono paginate (`?page=`, `?page_size=`, max 100).

### Autenticazione

| Metodo | Endpoint | Accesso |
|---|---|---|
| POST | `/api/users/register/` | pubblico |
| POST | `/api/auth/login/` | pubblico |
| POST | `/api/auth/logout/` | autenticato |
| POST | `/api/auth/token/refresh/` | pubblico |
| POST | `/api/auth/token/verify/` | pubblico |
| POST | `/api/auth/google/` | pubblico |

Il login restituisce `access` (1 ora) e `refresh` (7 giorni). I refresh token
ruotano e il precedente viene messo in blacklist, quindi il client deve
sostituirlo a ogni rinnovo.

### Utenti e moderazione

| Metodo | Endpoint | Accesso |
|---|---|---|
| GET / PATCH | `/api/users/me/` | autenticato |
| GET | `/api/users/` | admin — `?search=` `?status=active\|banned\|admin` |
| POST | `/api/users/admins/` | admin — crea un altro admin |
| PATCH | `/api/users/<id>/ban/` | admin — `{"banned": true, "reason": "..."}` |
| PATCH | `/api/users/<id>/mute/` | admin — `{"hours": 24, "reason": "..."}` |

Il ban disattiva l'account. Il mute è a tempo: l'utente continua a leggere e a
mettere like ma non può pubblicare finché non scade. `hours: 0` lo revoca.
Un amministratore non può essere bannato, né può applicare provvedimenti a sé
stesso.

### Articoli

| Metodo | Endpoint | Accesso |
|---|---|---|
| GET | `/api/articles/` | pubblico — `?category=` `?tag=` `?search=` |
| POST | `/api/articles/` | admin (multipart per la copertina) |
| GET | `/api/articles/drafts/` | admin |
| GET | `/api/articles/<slug>/` | pubblico (le bozze solo agli admin) |
| PUT / PATCH / DELETE | `/api/articles/<slug>/` | admin |
| PATCH | `/api/articles/<slug>/publish/` | admin — `{"published": true}` |
| GET / POST | `/api/articles/categories/` | lettura pubblica, scrittura admin |
| GET / POST | `/api/articles/tags/` | lettura pubblica, scrittura admin |

Il dettaglio di un articolo espone `discussion`, che punta al topic del forum
collegato quando esiste.

### Forum

| Metodo | Endpoint | Accesso |
|---|---|---|
| GET / POST | `/api/forum/categories/` | lettura pubblica, scrittura admin |
| GET | `/api/forum/threads/` | pubblico — `?category=` `?article=` `?search=` |
| POST | `/api/forum/threads/` | autenticato, non silenziato |
| GET | `/api/forum/threads/<slug>/` | pubblico |
| PUT / PATCH / DELETE | `/api/forum/threads/<slug>/` | autore o admin |
| PATCH | `/api/forum/threads/<slug>/pin/` | admin |
| PATCH | `/api/forum/threads/<slug>/close/` | admin |
| GET / POST | `/api/forum/threads/<slug>/posts/` | lettura pubblica, scrittura autenticata |
| GET | `/api/forum/posts/<id>/` | pubblico |
| PUT / PATCH / DELETE | `/api/forum/posts/<id>/` | autore o admin |
| POST | `/api/forum/posts/<id>/like/` | autenticato |
| POST | `/api/forum/posts/<id>/pin/` | autore del thread o admin |
| GET / POST | `/api/forum/posts/<id>/replies/` | lettura pubblica, scrittura autenticata |
| PUT / PATCH / DELETE | `/api/forum/replies/<id>/` | autore o admin |
| POST | `/api/forum/replies/<id>/like/` | autenticato |

Per aprire un topic a partire da un articolo basta passare `article_id` nel
corpo della POST su `/api/forum/threads/`. Sono accettati solo articoli
pubblicati.

## Note operative

- Le azioni di stato (`ban`, `mute`, `publish`, `pin`, `close`) sono esplicite,
  non toggle: ripetere la stessa chiamata è idempotente. Serve a evitare che
  due moderatori che agiscono insieme si annullino a vicenda.
- `DEBUG`, `ALLOWED_HOSTS` e le origini CORS arrivano dall'ambiente. Con
  `DEBUG=False` si attivano HSTS, redirect HTTPS e cookie `Secure`.
