import { createClient, SupabaseClient } from '@supabase/supabase-js'

let supabase: SupabaseClient | null = null

export function initSupabaseAuth() {
  try {
    const url = (import.meta as any)?.env?.VITE_SUPABASE_URL || ''
    const anon = (import.meta as any)?.env?.VITE_SUPABASE_ANON_KEY || ''
    if (!url || !anon) return
    supabase = createClient(url, anon)
    supabase.auth.onAuthStateChange((_event, session) => {
      const token = session?.access_token || ''
      try { (globalThis as any).__SUPABASE_JWT__ = token } catch {}
      try { if (token) localStorage.setItem('supabase_token', token) } catch {}
    })
    ;(async () => {
      const { data } = await supabase!.auth.getSession()
      const token = data?.session?.access_token || ''
      try { (globalThis as any).__SUPABASE_JWT__ = token } catch {}
      try { if (token) localStorage.setItem('supabase_token', token) } catch {}
    })()
  } catch {}
}

export function getSupabase(): SupabaseClient | null {
  return supabase
}
