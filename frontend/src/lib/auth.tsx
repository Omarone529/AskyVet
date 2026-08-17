import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api, setSessionExpiredHandler, tokens } from './api'
import type { CurrentUser, LoginResponse } from '@/types'

interface AuthContextValue {
  user: CurrentUser | null
  /** true finché non sappiamo se la sessione salvata è ancora valida. */
  initialising: boolean
  isAdmin: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithGoogle: (accessToken: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

export interface RegisterData {
  email: string
  username: string
  password: string
  password_confirm: string
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [initialising, setInitialising] = useState(true)

  const loadUser = useCallback(async () => {
    const me = await api.get<CurrentUser>('/api/users/me/')
    setUser(me)
  }, [])

  // Il token nel localStorage può essere scaduto o revocato: l'unico modo di
  // saperlo è chiedere al server. Finché non risponde non si decide cosa
  // mostrare, altrimenti una pagina protetta lampeggerebbe verso il login.
  useEffect(() => {
    if (!tokens.access()) {
      setInitialising(false)
      return
    }
    loadUser()
      .catch(() => {
        tokens.clear()
        setUser(null)
      })
      .finally(() => setInitialising(false))
  }, [loadUser])

  // api.ts avvisa da qui quando un rinnovo fallisce: lo stato React va
  // svuotato o l'interfaccia continuerebbe a mostrare l'utente come loggato.
  useEffect(() => {
    setSessionExpiredHandler(() => setUser(null))
    return () => setSessionExpiredHandler(() => {})
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post<LoginResponse>(
      '/api/auth/login/',
      { email, password },
      { skipAuth: true },
    )
    tokens.save(data)
    setUser(data.user)
  }, [])

  const loginWithGoogle = useCallback(async (accessToken: string) => {
    const data = await api.post<LoginResponse>(
      '/api/auth/google/',
      { access_token: accessToken },
      { skipAuth: true },
    )
    tokens.save(data)
    setUser(data.user)
  }, [])

  const register = useCallback(
    async (data: RegisterData) => {
      await api.post('/api/users/register/', data, { skipAuth: true })
      // La registrazione non restituisce token: si entra subito con le stesse
      // credenziali, così l'utente non deve digitarle una seconda volta.
      await login(data.email, data.password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    const refresh = tokens.refresh()
    try {
      // Mette in blacklist il refresh lato server. Se fallisce (token già
      // scaduto) non importa: la sessione locale va comunque chiusa.
      if (refresh) await api.post('/api/auth/logout/', { refresh })
    } catch {
      // Ignorato di proposito, vedi sopra.
    } finally {
      tokens.clear()
      setUser(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      initialising,
      isAdmin: user?.is_admin ?? false,
      login,
      loginWithGoogle,
      register,
      logout,
      refreshUser: loadUser,
    }),
    [user, initialising, login, loginWithGoogle, register, logout, loadUser],
  )

  return <AuthContext value={value}>{children}</AuthContext>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth va usato dentro <AuthProvider>.')
  }
  return context
}
