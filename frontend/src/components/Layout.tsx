import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { Avatar, Button, cx } from './ui'
import { formatDateTime } from '@/lib/format'
import { useAuth } from '@/lib/auth'

const NAV = [
  { to: '/', label: 'Articoli', end: true },
  { to: '/forum', label: 'Forum', end: false },
]

function navClass({ isActive }: { isActive: boolean }): string {
  return cx(
    'rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-brand-50 text-brand-900' : 'text-ink-700 hover:bg-slate-100',
  )
}

function UserMenu() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link to="/login">
          <Button variant="ghost" size="sm">
            Accedi
          </Button>
        </Link>
        <Link to="/registrati">
          <Button size="sm">Registrati</Button>
        </Link>
      </div>
    )
  }

  const handleLogout = async () => {
    setOpen(false)
    await logout()
    navigate('/')
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-2 rounded-lg p-1 hover:bg-slate-100"
      >
        <Avatar username={user.username} src={user.avatar} size={32} />
        <span className="hidden text-sm font-medium text-ink-900 sm:inline">
          {user.username}
        </span>
      </button>

      {open && (
        <>
          {/* Sfondo trasparente: un clic fuori chiude il menu senza dover
              ascoltare gli eventi su tutto il documento. */}
          <div
            className="fixed inset-0 z-10"
            aria-hidden="true"
            onClick={() => setOpen(false)}
          />
          <div
            role="menu"
            className="absolute right-0 z-20 mt-2 w-52 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
          >
            <div className="border-b border-slate-100 px-4 py-2">
              <p className="truncate text-sm font-medium text-ink-900">
                {user.username}
              </p>
              <p className="truncate text-xs text-ink-500">{user.email}</p>
            </div>

            <Link
              to="/profilo"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-ink-700 hover:bg-slate-50"
            >
              Il mio profilo
            </Link>

            {user.is_admin && (
              <>
                <Link
                  to="/admin/articoli"
                  role="menuitem"
                  onClick={() => setOpen(false)}
                  className="block px-4 py-2 text-sm text-ink-700 hover:bg-slate-50"
                >
                  Gestione articoli
                </Link>
                <Link
                  to="/admin/utenti"
                  role="menuitem"
                  onClick={() => setOpen(false)}
                  className="block px-4 py-2 text-sm text-ink-700 hover:bg-slate-50"
                >
                  Gestione utenti
                </Link>
              </>
            )}

            <button
              type="button"
              role="menuitem"
              onClick={handleLogout}
              className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
            >
              Esci
            </button>
          </div>
        </>
      )}
    </div>
  )
}

/** Avviso persistente per chi è stato silenziato da un moderatore. */
function MuteNotice() {
  const { user } = useAuth()
  if (!user?.is_muted) return null

  return (
    <div className="bg-amber-100 text-amber-900">
      <div className="mx-auto max-w-5xl px-4 py-2 text-sm">
        Sei silenziato fino al <strong>{formatDateTime(user.muted_until)}</strong>.
        Puoi leggere e mettere like, ma non pubblicare.
      </div>
    </div>
  )
}

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Primo elemento focalizzabile: chi naviga da tastiera salta il menu. */}
      <a
        href="#contenuto"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow"
      >
        Vai al contenuto
      </a>

      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-5xl items-center gap-4 px-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl">🐾</span>
            <span className="text-lg font-bold tracking-tight text-ink-900">
              AskyVet
            </span>
          </Link>

          <nav className="ml-2 flex items-center gap-1">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto">
            <UserMenu />
          </div>
        </div>
      </header>

      <MuteNotice />

      <main id="contenuto" className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-ink-500">
          AskyVet — divulgazione veterinaria.
        </div>
      </footer>
    </div>
  )
}
