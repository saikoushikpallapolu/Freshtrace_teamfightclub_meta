import { useEffect, useState } from 'react'
import { jsonPost, request, sampleImageUrl } from '../../api/client'

export default function SamplePicker({ batchId, onImported }) {
  const [samples, setSamples] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => {
    let cancelled = false
    request('/samples').then((items) => { if (!cancelled) setSamples(items) })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [])
  async function choose(sample) {
    setBusy(true); setError('')
    try {
      const observation = await request(`/samples/${sample.sample_id}/import`, jsonPost({ batch_id: batchId }, crypto.randomUUID()))
      await onImported(observation)
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  return <details className="sample-picker"><summary>Try a real public sample photo</summary>
    <p>These are development examples, not an accuracy benchmark. Importing a photo is free; analysis uses Meta credits.</p>
    {error && <p role="alert">{error}</p>}
    <div className="sample-grid">{samples.map((sample) => <article key={sample.sample_id}>
      <img src={sampleImageUrl(sample.sample_id)} alt={sample.title} loading="lazy" />
      <h3>{sample.title}</h3><p>{sample.description}</p>
      <button disabled={busy} onClick={() => choose(sample)}>{busy ? 'Importing…' : 'Add sample to this batch'}</button>
      <small>Photo: {sample.author} · <a href={sample.source_url} target="_blank" rel="noreferrer">Source</a> · <a href={sample.license_url} target="_blank" rel="noreferrer">{sample.license}</a></small>
    </article>)}</div>
  </details>
}
