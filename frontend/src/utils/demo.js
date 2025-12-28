export const isDemoMode =
  String(import.meta.env.VITE_DEMO_MODE || '')
    .trim()
    .toLowerCase() === 'true'

