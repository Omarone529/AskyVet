# Frontend AskyVet

Applicazione React (Vite + TypeScript + Tailwind 4) che consuma l'API Django in
`../backend`.

## Avvio

```bash
cp .env.example .env      # completa VITE_GOOGLE_CLIENT_ID se serve
npm install
npm run dev               # http://localhost:5173
```

Il backend deve essere in ascolto su `http://localhost:8000`. La porta 5173 è
fissata in `vite.config.ts`: è quella autorizzata in `CORS_ALLOWED_ORIGINS` lato
Django, e su una porta diversa il browser bloccherebbe ogni chiamata.

| Comando | Cosa fa |
|---|---|
| `npm run dev` | server di sviluppo con hot reload |
| `npm run build` | typecheck + build di produzione in `dist/` |
| `npm run typecheck` | solo controllo dei tipi |
| `npm run lint` | oxlint |

## Struttura

```
src/
├── main.tsx           router e provider
├── index.css          Tailwind + token del tema
├── types.ts           tipi che rispecchiano i serializer DRF
├── lib/
│   ├── api.ts         client HTTP, JWT e rinnovo automatico
│   ├── auth.tsx       AuthProvider e useAuth
│   ├── google.ts      accesso con Google (GIS)
│   ├── hooks.ts       useApi, useDebounced
│   └── format.ts      date e testi in italiano
├── components/
│   ├── Layout.tsx     header, menu utente, avviso di mute
│   ├── ProtectedRoute.tsx
│   └── ui.tsx         Button, Field, Card, Badge, Alert, Pagination…
└── pages/             una per rotta
```

## Rotte

| Percorso | Accesso |
|---|---|
| `/` | pubblico — elenco articoli |
| `/articoli/:slug` | pubblico — articolo e link alla discussione |
| `/forum` | pubblico — elenco topic, apertura nuovo topic se loggato |
| `/forum/:slug` | pubblico — post, risposte, like |
| `/login`, `/registrati` | pubblico |
| `/profilo` | autenticato |
| `/admin/articoli`, `/admin/utenti` | solo amministratori |

## Note di implementazione

**Autenticazione.** I token stanno in `localStorage`. Su 401 il client rinnova
l'access token e ritenta la richiesta una volta sola. Il backend ruota i refresh
token e mette in blacklist il precedente, quindi `api.ts` salva sempre quello
nuovo; i rinnovi concorrenti condividono una sola promessa, altrimenti la prima
rotazione invaliderebbe le altre richieste in volo.

**Tipi.** `src/types.ts` rispecchia i serializer del backend. Se cambia un campo
lì, va aggiornato qui: è il punto in cui il disallineamento emerge in fase di
build invece che a pagina aperta.

**Sicurezza.** Il corpo degli articoli viene reso come testo, mai con
`dangerouslySetInnerHTML`. Le variabili `VITE_*` finiscono nel bundle e sono
visibili a chiunque: non vanno usate per segreti.
