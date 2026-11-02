import { useEffect, useRef, useState } from 'react'
import { jsonPost, mediaUrl, request } from '../api/client'
import './BatchWorkspace.css'
import InspectionPanel from '../components/evidence/InspectionPanel'
import SamplePicker from '../components/capture/SamplePicker'

function date(value) { return new Date(value).toLocaleString() }

export default function BatchWorkspace() {
  const [batches, setBatches] = useState([])
  const [selected, setSelected] = useState(() => new URLSearchParams(location.search).get('batch'))
  const [current, setCurrent] = useState(null)
  const [history, setHistory] = useState([])
  const [activeObservation, setActiveObservation] = useState(() => new URLSearchParams(location.search).get('observation'))
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const batchAttempt = useRef(null)
  const captureAttempt = useRef(null)
  const fileInput = useRef(null)
  const selectedBatchRef = useRef(selected)

  useEffect(() => {
    return () => { if (preview) URL.revokeObjectURL(preview) }
  }, [preview])

  useEffect(() => {
    let cancelled = false
    Promise.all([request('/batches?limit=100'), selected ? request(`/batches/${selected}`) : null,
      selected ? request(`/batches/${selected}/observations?limit=100`) : []])
      .then(([list, batch, observations]) => {
        if (!cancelled) { setBatches(list); setCurrent(batch); setHistory(observations) }
      })
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [selected])

  function openBatch(id) {
    if (id === selected) return
    const url = new URL(location.href)
    url.searchParams.set('batch', id)
    url.searchParams.delete('observation')
    window.history.replaceState({}, '', url)
    selectedBatchRef.current = id
    setSelected(id)
    setLoading(true)
    setError('')
    setCurrent(null)
    setHistory([])
    setActiveObservation(null)
    setFile(null)
    setPreview('')
    captureAttempt.current = null
    setNotice('')
  }

  async function createBatch(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const payload = { label: form.get('label'), produce_type: 'tomato',
      quantity: Number(form.get('quantity')), quantity_unit: form.get('unit') }
    const fingerprint = JSON.stringify(payload)
    if (batchAttempt.current?.fingerprint !== fingerprint)
      batchAttempt.current = { fingerprint, key: crypto.randomUUID() }
    setBusy(true); setError('')
    try {
      const result = await request('/batches', jsonPost(payload, batchAttempt.current.key))
      batchAttempt.current = null
      event.target.reset()
      openBatch(result.batch_id)
      setBatches(await request('/batches?limit=100'))
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  async function saveCapture(event) {
    event.preventDefault()
    if (!file || !current) return
    const batchId = current.batch_id
    if (!captureAttempt.current) captureAttempt.current = {
      mediaKey: crypto.randomUUID(), observationKey: crypto.randomUUID(),
      capturedAt: new Date().toISOString(), mediaId: null,
    }
    const attempt = captureAttempt.current
    setBusy(true); setError(''); setNotice('')
    try {
      if (!attempt.mediaId) {
        const media = await request(`/batches/${batchId}/media`, { method: 'POST',
          headers: { 'Content-Type': file.type, 'Idempotency-Key': attempt.mediaKey }, body: file })
        attempt.mediaId = media.media_id
      }
      const savedObservation = await request(`/batches/${batchId}/observations`, jsonPost({ media_id: attempt.mediaId,
        captured_at: attempt.capturedAt, source: 'user_capture' }, attempt.observationKey))
      setHistory(await request(`/batches/${batchId}/observations?limit=100`))
      openObservation(savedObservation.observation_id)
      setFile(null); setPreview(''); captureAttempt.current = null
      if (fileInput.current) fileInput.current.value = ''
      setNotice('Photo saved. Choose Analyse tomatoes in its history card to run the models.')
    } catch (err) { setError(`${err.message}. You can retry saving the same photo.`) }
    finally { setBusy(false) }
  }

  function openObservation(id) {
    const url = new URL(location.href)
    url.searchParams.set('observation', id)
    window.history.replaceState({}, '', url)
    setActiveObservation(id)
  }

  const shownObservation = history.some((o) => o.observation_id === activeObservation) ? activeObservation : history[0]?.observation_id

  return <div className="batch-workspace">
    <header className="batch-header"><a href="/" className="batch-wordmark">Produce workspace</a>
      <a href="?view=device">Device dashboard ↗</a></header>
    <main>
      <div className="batch-intro"><span className="batch-eyebrow">BUILD 02 / VISUAL INSPECTION</span>
        <h1>Every inspection starts<br />with a batch.</h1>
        <p>Register your tomatoes, capture a clear photo and keep the evidence together.</p></div>
      {error && <div role="alert" className="batch-error">{error}</div>}
      {notice && <div role="status" className="batch-notice">{notice}</div>}
      <div className="batch-layout"><aside>
        <section className="batch-card"><h2>Register a batch</h2>
          <form onSubmit={createBatch}>
            <label>Batch label<input name="label" required maxLength={120} placeholder="e.g. Morning delivery · Tray A" disabled={busy} /></label>
            <div className="batch-fields"><label>Quantity<input name="quantity" type="number" min="0.001" max="1000000" step="any" required disabled={busy} /></label>
              <label>Unit<select name="unit" disabled={busy}><option value="items">Tomatoes</option><option value="kg">Kilograms</option></select></label></div>
            <button disabled={busy} type="submit">{busy ? 'Saving…' : 'Create batch'}</button>
          </form></section>
        <section className="batch-card"><h2>Your batches</h2>
          {loading && <p role="status">Loading saved records…</p>}
          {!loading && batches.length === 0 && <p>No batches yet. Register your first tray above.</p>}
          <nav aria-label="Batches">{batches.map((batch) => <button type="button" key={batch.batch_id}
            className={`batch-choice ${batch.batch_id === selected ? 'selected' : ''}`} disabled={busy}
            onClick={() => openBatch(batch.batch_id)}><strong>{batch.label}</strong>
            <span>{batch.quantity} {batch.quantity_unit} · {date(batch.created_at)}</span></button>)}</nav>
          {batches.length === 100 && <p>Showing the latest 100 batches.</p>}
        </section></aside>
        <div>{current ? <>
          <section className="batch-card"><span className="batch-eyebrow">BATCH PASSPORT</span>
            <h2>{current.label}</h2><p>{current.quantity} {current.quantity_unit} of {current.produce_type}</p>
            <p className="batch-id">ID {current.batch_id}</p>
            <div className="batch-evidence-status"><span>Camera: SAM + Spark</span><span>Sensor: not linked</span><span>History: saved</span></div>
          </section>
          <section className="batch-card"><h2>Capture evidence</h2>
            <p>Use a clear overhead photo. Keep the tomatoes in one layer where possible.</p>
            <form onSubmit={saveCapture}><label>Take or choose a photo<input ref={fileInput} type="file"
              accept="image/jpeg,image/png" disabled={busy} onChange={(event) => {
                const next = event.target.files?.[0] || null
                captureAttempt.current = null
                if (next && (!['image/jpeg', 'image/png'].includes(next.type) || next.size > 10 * 1024 * 1024)) {
                  setError('Choose a JPEG or PNG no larger than 10 MiB.'); setFile(null); setPreview(''); return
                }
                setError(''); setFile(next); setPreview(next ? URL.createObjectURL(next) : '')
              }} /></label>
              {preview && <img className="batch-preview" src={preview} alt="Selected photo before saving" />}
              <button disabled={!file || busy}>{busy ? 'Saving…' : 'Save photo to batch'}</button>
            </form><small>JPEG or PNG · up to 10 MiB and 20 megapixels. Photos are saved locally.</small>
            <SamplePicker batchId={current.batch_id} onImported={async (observation) => {
              const observations = await request(`/batches/${current.batch_id}/observations?limit=100`)
              if (selectedBatchRef.current !== current.batch_id) return
              setHistory(observations)
              openObservation(observation.observation_id)
              setNotice('Public test photo added. Its source is recorded; run analysis in its history card.')
            }} />
          </section>
          <section className="batch-card"><h2>Evidence history</h2>
            <p>Saved observations remain available when you reopen this batch.</p>
            {history.length === 0 && <div className="batch-empty">No observations yet. Add the first photo above.</div>}
            <div className="batch-history">{history.map((observation) => <article key={observation.observation_id} className="observation-card">
              <div className="observation-summary">
              <a href={mediaUrl(current.batch_id, observation.media_id)} target="_blank" rel="noreferrer">
                <img src={mediaUrl(current.batch_id, observation.media_id)} alt={`Batch observation captured ${date(observation.captured_at)}`} loading="lazy" /></a>
              <div><strong>{date(observation.captured_at)}</strong><p>{observation.source === 'fixture' ? `Public test sample · ${observation.sample_id || 'fixture'} · added at this time` : 'User capture'}</p>
                <small>Human review remains separate from model evidence.</small>
                <button className="secondary-button" disabled={shownObservation === observation.observation_id} onClick={() => openObservation(observation.observation_id)}>{shownObservation === observation.observation_id ? 'Viewing this inspection' : 'Open inspection'}</button></div></div>
              {shownObservation === observation.observation_id && <InspectionPanel batchId={current.batch_id} observationId={observation.observation_id} sampleId={observation.sample_id} />}
              </article>)}</div>
            {history.length === 100 && <p>Showing the latest 100 observations.</p>}
          </section>
        </> : <section className="batch-card batch-welcome"><span className="batch-eyebrow">ONE CONNECTED WORKFLOW</span>
          <h2>Capture. Inspect. Follow up.</h2><p>Create or select a batch to begin its evidence history.</p>
          <ol><li>Keep each tray's photos together.</li><li>Inspect individual tomatoes with SAM and Spark.</li>
            <li>Attach validated sensor measurements and record confirmed actions.</li></ol>
          <div className="batch-empty">No inspection score is calculated from missing evidence.</div>
        </section>}</div>
      </div>
    </main><footer>Local prototype · SAM finds tomatoes, Spark observes visible condition, you confirm the findings. Sensor sessions and Wonder planning are upcoming.</footer>
  </div>
}
