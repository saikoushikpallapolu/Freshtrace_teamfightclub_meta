import { useEffect, useRef, useState } from 'react'
import { artifactUrl, jsonPost, request } from '../../api/client'

const labels = { inspect: 'Inspect this tomato', no_visible_concern: 'No visible concern', unclear: 'Needs another view' }
const errors = {
  too_many_objects_use_smaller_tray: 'More than 32 candidate regions were found. Photograph a smaller group or upload a crop.',
  no_tomatoes_detected: 'SAM did not find a tomato. Try a closer, clearer photo.',
  worker_interrupted: 'The worker stopped before finishing. This attempt was not automatically retried.',
  provider_authentication_failed: 'Meta rejected the server key. Update it on the server and restart the API.',
  provider_access_denied: 'The server key does not have access to this model.',
  provider_rate_limited: 'Meta temporarily limited requests. Retry later.',
}

function ItemReview({ item, latest, onReview, disabled }) {
  const [category, setCategory] = useState(latest?.category || item.category)
  const [note, setNote] = useState('')
  return <form className="item-review" onSubmit={(event) => {
    event.preventDefault(); onReview({ object_id: item.object_id, category, note })
  }}><label>Your inspection<select value={category} onChange={(e) => setCategory(e.target.value)} disabled={disabled}>
    {Object.entries(labels).map(([key, label]) => <option value={key} key={key}>{label}</option>)}
  </select></label><label>Inspection note<input value={note} onChange={(e) => setNote(e.target.value)} required maxLength={500}
    placeholder="What did you see?" disabled={disabled} /></label>
    <button disabled={disabled}>Save human review</button>
    {latest && <small>Latest human review: {labels[latest.category]} — {latest.note}</small>}
  </form>
}

export default function InspectionPanel({ batchId, observationId, sampleId }) {
  const path = `/batches/${batchId}/observations/${observationId}`
  const [data, setData] = useState(null)
  const [capabilities, setCapabilities] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [showOverlay, setShowOverlay] = useState(true)
  const [selected, setSelected] = useState(null)
  const [categoryFilter, setCategoryFilter] = useState('inspect')
  const [source, setSource] = useState(null)
  const hitMap = useRef(null)

  useEffect(() => {
    let cancelled = false
    async function refresh() {
      try {
        const [result, supported, samples] = await Promise.all([request(`${path}/analysis`), request('/capabilities'), sampleId ? request('/samples') : []])
        if (!cancelled) { setData(result); setCapabilities(supported); setSource(samples.find((s) => s.sample_id === sampleId) || null); setError('') }
      } catch (err) { if (!cancelled) setError(err.message) }
    }
    refresh()
    return () => { cancelled = true }
  }, [path, sampleId])

  const jobStatus = data?.job?.status
  useEffect(() => {
    if (jobStatus !== 'complete') return
    const image = new Image()
    let cancelled = false
    image.onload = () => {
      if (cancelled) return
      const canvas = document.createElement('canvas')
      canvas.width = image.naturalWidth; canvas.height = image.naturalHeight
      const context = canvas.getContext('2d', { willReadFrequently: true })
      context.drawImage(image, 0, 0)
      hitMap.current = context
    }
    image.src = artifactUrl(batchId, observationId, 'hit_map.png')
    return () => { cancelled = true; hitMap.current = null }
  }, [batchId, observationId, jobStatus])
  useEffect(() => {
    if (!['queued', 'running'].includes(jobStatus)) return
    let cancelled = false
    const timer = setInterval(async () => {
      try {
        const result = await request(`${path}/analysis`)
        if (!cancelled) { setData(result); setError('') }
      } catch (err) { if (!cancelled) setError(err.message) }
    }, 2500)
    return () => { cancelled = true; clearInterval(timer) }
  }, [path, jobStatus])

  async function run(retry = false) {
    setBusy(true); setError('')
    try {
      const job = await request(`${path}/analysis${retry ? '/retry' : ''}`, { method: 'POST' })
      setData((old) => ({ ...old, job }))
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  async function review(payload) {
    setBusy(true); setError('')
    try {
      await request(`${path}/reviews`, jsonPost(payload, crypto.randomUUID()))
      setData(await request(`${path}/analysis`))
    } catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }

  const job = data?.job
  const result = job?.result
  const objects = result?.objects || []
  const chosen = objects.find((obj) => obj.object_id === selected)
  const displayed = chosen ? [chosen] : objects.filter((item) => categoryFilter === 'all' || item.category === categoryFilter)
  const counts = Object.fromEntries(Object.keys(labels).map((key) => [key, objects.filter((o) => o.category === key).length]))
  return <div className="inspection-panel">
    {source && <small className="sample-credit">Photo: {source.author} · <a href={source.source_url} target="_blank" rel="noreferrer">Original source</a> · <a href={source.license_url} target="_blank" rel="noreferrer">{source.license}</a>. Analysis crops and overlays are derivatives. No independent reference labels.</small>}
    {error && <p role="alert" className="batch-error">{error}</p>}
    {!data && !error && <p role="status">Loading inspection…</p>}
    {data && !job && <div className="analysis-ready"><p>Inspect this photo with SAM and Muse Spark.</p>
      <button onClick={() => run()} disabled={busy || !capabilities?.live_analysis}>Analyse tomatoes</button>
      <small>{capabilities?.live_analysis ? 'Runs live Meta inference and uses API credits. No sensor measurement is included.' :
        'Live analysis is not configured on the server. Photos remain saved.'}</small></div>}
    {job && ['queued', 'running'].includes(job.status) && <div role="status" className="batch-empty">
      {job.status === 'queued' ? 'Analysis queued' : 'SAM → item crops → Spark: analysis running'}.
      {capabilities?.live_analysis ? ' You can reopen this batch while processing continues.' : ' Processing waits until the server is configured with a key and restarted.'}</div>}
    {job?.status === 'failed' && <div className="batch-error"><p>Analysis did not complete. {errors[job.error_code] || 'The response could not be validated. No inspection result is available.'}</p>
      <button onClick={() => run(true)} disabled={busy || !capabilities?.live_analysis}>Retry live analysis</button>
      <small>Retry starts another attempt and may use more credits. No automatic retries are made.</small></div>}
    {job?.status === 'complete' && result && <>
      <div className="inspection-heading"><h3>Item inspection</h3><span className="live-badge">{result.mode === 'live_meta' ? 'Saved live Meta result' : 'Test fixture · not live'} · attempt {job.attempt}</span></div>
      <div className="inspection-counts"><span className="inspect">{counts.inspect} to inspect</span>
        <span className="no_visible_concern">{counts.no_visible_concern} without visible concern</span>
        <span className="unclear">{counts.unclear} unclear</span></div>
      <p className="inspection-help">SAM finds individual tomatoes. Spark describes their visible condition. Select a numbered region to inspect its evidence.</p>
      <button className="secondary-button" onClick={() => setShowOverlay(!showOverlay)}>{showOverlay ? 'Show original analysis image' : 'Show item overlay'}</button>
      <button className="inspection-image" aria-label="Select a tomato on the image" onClick={(event) => {
        if (!hitMap.current) return
        const rect = event.currentTarget.getBoundingClientRect()
        const x = event.detail === 0 ? rect.width / 2 : event.clientX - rect.left
        const y = event.detail === 0 ? rect.height / 2 : event.clientY - rect.top
        const px = Math.min(result.width - 1, Math.max(0, Math.floor(x / rect.width * result.width)))
        const py = Math.min(result.height - 1, Math.max(0, Math.floor(y / rect.height * result.height)))
        try { const index = hitMap.current.getImageData(px, py, 1, 1).data[0] - 1
          if (objects[index]) setSelected(objects[index].object_id)
        } catch { setError('Image picking is unavailable. Use the numbered item buttons below.') }
      }}><img src={artifactUrl(batchId, observationId, showOverlay ? 'inspection_overlay.jpg' : 'analysis.jpg')}
        alt={showOverlay ? 'Tomatoes segmented and labeled with image-local IDs' : 'Image used for this analysis'} /></button>
      <div className="object-selector" aria-label="Select an item">{objects.map((obj) => <button key={obj.object_id}
        className={`object-chip ${obj.category} ${selected === obj.object_id ? 'active' : ''}`}
        aria-label={`Select ${obj.object_id}: ${labels[obj.category]}`} aria-pressed={selected === obj.object_id}
        onClick={() => setSelected(obj.object_id)}>{obj.object_id}</button>)}</div>
      <div className="object-selector" aria-label="Filter item evidence">{[['inspect', 'Inspection flags'], ['unclear', 'Unclear items'], ['all', 'All items']].map(([value, label]) =>
        <button className="secondary-button" key={value} aria-pressed={!chosen && categoryFilter === value}
          onClick={() => { setSelected(null); setCategoryFilter(value) }}>{label}</button>)}</div>
      {chosen && <button className="secondary-button" onClick={() => { setSelected(null); setCategoryFilter('all') }}>Show all {objects.length} items</button>}
      {displayed.length === 0 && <p>No items in this category. Check unclear items and visibility limits before deciding what to do.</p>}
      <div className="inspection-items">{displayed.map((item) => {
        const latest = data.reviews.filter((r) => r.object_id === item.object_id).at(-1)
        return <section key={item.object_id} className={`inspection-item ${item.category}`}>
          <div className="item-evidence"><img src={artifactUrl(batchId, observationId, item.crop_file)} alt={`Context crop for ${item.object_id}`} loading="lazy" />
            <div><h4>{item.object_id} · {labels[item.category]}</h4>
              <ul>{item.observations.map((text, i) => <li key={i}>{text}</li>)}</ul>
              <small>Visibility: {item.visibility_limits.join(' ')}</small></div></div>
          <details><summary>Confirm or correct this observation</summary>
            <ItemReview item={item} latest={latest} onReview={review} disabled={busy} /></details>
          {latest && <p className="review-saved">Review saved: {labels[latest.category]}. {latest.note} Model evidence is retained.</p>}
        </section>
      })}</div>
      <div className="batch-empty"><strong>Investigation next step</strong><p>{counts.inspect ? 'Inspect the flagged tomatoes in person. Record your review before deciding what to remove.' :
        counts.unclear ? 'Take another view to resolve hidden surfaces and ambiguous items.' : 'Continue routine inspection; this photo cannot establish freshness or food safety.'}</p>
        <small>{result.scene_limits.join(' ')} Sensor evidence: unavailable. No fused score or remaining-life estimate is calculated.</small></div>
      <details className="model-receipts"><summary>Model receipts and provenance</summary>
        <p>Prompt {result.prompt_version}. Receipts include all attempts. IDs refer only to this photo. Responses are model observations, not independent labels.</p>
        {data.calls.map((call, i) => <p key={i}><strong>{call.model}</strong> · {call.status} · {(call.latency_ms / 1000).toFixed(1)} s<br />
          <code>{call.response_id || 'No response ID returned'}</code><br />Prompt {call.prompt_version} · {call.input_tokens ?? '—'} input / {call.output_tokens ?? '—'} output tokens</p>)}
        <small>Suggested next steps are deterministic application rules. Wonder planning will be added after validated sensor sessions.</small>
      </details>
    </>}
  </div>
}
