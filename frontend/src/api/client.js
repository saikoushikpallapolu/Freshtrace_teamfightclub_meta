const base = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

export const mediaUrl = (batchId, mediaId) =>
  `${base}/api/batches/${batchId}/media/${mediaId}/content`

export const artifactUrl = (batchId, observationId, filename) =>
  `${base}/api/batches/${batchId}/observations/${observationId}/artifacts/${filename}`

export const sampleImageUrl = (sampleId) => `${base}/api/samples/${sampleId}/image`

export async function request(path, options = {}) {
  const response = await fetch(`${base}/api${path}`, options)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = typeof body.detail === 'string' ? body.detail :
        body.detail?.map((error) => error.msg).join('; ') || message
    } catch { /* Preserve the HTTP status when the response is not JSON. */ }
    throw new Error(message)
  }
  return response.json()
}

export function jsonPost(payload, key) {
  return { method: 'POST', headers: { 'Content-Type': 'application/json',
    'Idempotency-Key': key }, body: JSON.stringify(payload) }
}
