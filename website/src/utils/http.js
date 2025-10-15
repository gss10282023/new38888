export async function safeJson(response) {
  if (!response) return null
  if (response.status === 204) return null
  try {
    return await response.json()
  } catch {
    return null
  }
}
