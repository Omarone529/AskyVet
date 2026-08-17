import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    // import.meta.dirname e non __dirname: quest'ultimo non esiste nei moduli
    // ESM e Vite avverte che smetterà di supportarlo.
    alias: { '@': path.resolve(import.meta.dirname, './src') },
  },
  server: {
    // Fissa, non "la prima libera": è l'origine autorizzata in
    // CORS_ALLOWED_ORIGINS lato Django. Su una porta diversa il browser
    // bloccherebbe ogni chiamata all'API.
    port: 5173,
    strictPort: true,
  },
})
