import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api/client'
import {
  formatScanTime,
  isScanProcessing,
  orderScans,
  scanStatusKind,
  scanStatusLabel,
} from '../utils/productJourneyUi'

function ScanRow({ scan, latest = false, onCancelled }) {
  const time = scan.completed_at || scan.started_at
  const [cancelState, setCancelState] = useState('idle')
  const cancel = async () => {
    if (!window.confirm(`Cancel "${scan.scan_name || `scan ${scan.id}`}"? The work done so far is discarded and the scan is marked Cancelled.`)) return
    setCancelState('sending')
    try {
      const outcome = await api.postJson(`/api/scans/${scan.id}/cancel`, {})
      setCancelState(outcome.status === 'CANCELLED' ? 'idle' : 'requested')
      onCancelled?.()
    } catch (e) {
      // 409: it finished or was cancelled meanwhile; the refreshed row shows which.
      setCancelState(e.status === 409 ? 'idle' : 'error')
      if (e.status === 409) onCancelled?.()
    }
  }
  return <article className={`history-row ${latest ? 'latest-scan' : ''}`}>
    <div>
      <p className="eyebrow">{latest ? 'Latest scan' : `Scan ${scan.id}`}</p>
      <h3>{scan.scan_name || `Inventory scan ${scan.id}`}</h3>
      <div className="history-meta">
        <span className={`scan-state ${scanStatusKind(scan.status)}`}>{scanStatusLabel(scan.status)}</span>
        <span>{Number(scan.total_records || 0).toLocaleString()} records</span>
        <span>{scan.completed_at ? 'Completed ' : 'Started '}{formatScanTime(time)}</span>
      </div>
    </div>
    <div className="history-actions">
      {isScanProcessing(scan.status) && <button type="button" className="danger" onClick={cancel} disabled={cancelState === 'sending' || cancelState === 'requested'}>
        {cancelState === 'sending' || cancelState === 'requested' ? 'Cancelling…' : 'Cancel scan'}
      </button>}
      <Link className="button secondary" to={`/scans/${scan.id}`}>Open results</Link>
    </div>
    {cancelState === 'error' && <p className="warning" role="alert">The cancel request did not reach the server. Try again.</p>}
  </article>
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [health, setHealth] = useState(null)
  const [scans, setScans] = useState(null)
  const [historyError, setHistoryError] = useState(false)

  const loadScans = useCallback(() => api.get('/api/scans').then(
    history => { setScans(orderScans(history)); setHistoryError(false) },
    () => { setScans(current => current || []); setHistoryError(true) },
  ), [])

  // A cancel request is honoured at the scan's next safe point, so poll
  // until no scan is processing any more.
  const processing = (scans || []).some(scan => isScanProcessing(scan.status))
  useEffect(() => {
    if (!processing) return undefined
    const timer = window.setInterval(loadScans, 5000)
    return () => window.clearInterval(timer)
  }, [processing, loadScans])

  useEffect(() => {
    let active = true
    Promise.allSettled([
      api.get('/api/diagnostics/summary'), api.get('/health'), api.get('/ready'), api.get('/api/scans'),
    ]).then(([diagnostics, service, readiness, history]) => {
      if (!active) return
      if (diagnostics.status === 'fulfilled') setData(diagnostics.value)
      if (service.status === 'fulfilled') setHealth({
        ...service.value,
        readiness: readiness.status === 'fulfilled' ? readiness.value.status : 'Readiness unavailable',
      })
      if (history.status === 'fulfilled') setScans(orderScans(history.value))
      else { setScans([]); setHistoryError(true) }
    })
    return () => { active = false }
  }, [])

  const latest = scans?.[0] || null
  const recent = scans?.slice(1) || []
  const completedCount = useMemo(
    () => (scans || []).filter(scan => String(scan.status).toUpperCase() === 'COMPLETED').length,
    [scans],
  )

  return <>
    <header><div><p className="eyebrow">Dashboard</p><h1>Inventory duplicate review</h1><p>Start a scan or reopen a previous result.</p></div><Link className="button" to="/new-scan">Start new scan</Link></header>
    <section className="banner"><b>Candidate detection, not automatic merging.</b> System groups support review decisions; human review remains authoritative.</section>
    <div className="cards">
      <article><label>Service</label><strong>{health?.status || 'Checking…'}</strong><small>{health?.readiness || ''}</small></article>
      <article><label>Total scans</label><strong>{scans?.length ?? data?.total_scans ?? '…'}</strong></article>
      <article><label>Completed scans</label><strong>{scans ? completedCount : '…'}</strong></article>
      <article><label>Human feedback</label><strong>{data?.total_feedback_records ?? '…'}</strong></article>
    </div>

    <section className="panel scan-history" aria-labelledby="latest-scan-heading">
      <div className="section-heading"><div><p className="eyebrow">Latest scan</p><h2 id="latest-scan-heading">Most recent activity</h2></div></div>
      {scans === null ? <p role="status" aria-live="polite">Loading scan history…</p> :
        historyError ? <div className="error" role="alert"><b>Scan history could not be loaded.</b><p>Check that the backend is running, then reload this page.</p></div> :
        latest ? <ScanRow scan={latest} latest onCancelled={loadScans} key={latest.id} /> : <div className="empty actionable-empty"><h3>No scans yet</h3><p>Start a new scan to create the first result.</p><Link className="button" to="/new-scan">Start a new scan</Link></div>}
    </section>

    <section className="panel scan-history" aria-labelledby="recent-scans-heading">
      <div className="section-heading"><div><p className="eyebrow">Recent scans</p><h2 id="recent-scans-heading">Previous scan history</h2></div><span>{scans?.length || 0} total</span></div>
      {scans !== null && scans.length > 0 && completedCount === 0 && <p className="warning">No completed scans are available yet. Processing and failed attempts remain listed below with their actual status.</p>}
      {scans === null ? <p role="status">Loading recent scans…</p> : recent.length ? <div className="history-list">{recent.map(scan => <ScanRow scan={scan} key={scan.id} onCancelled={loadScans} />)}</div> :
        <div className="empty actionable-empty"><h3>{latest ? 'No earlier scans' : 'History is empty'}</h3><p>{latest ? 'The latest scan is currently the only scan.' : 'Completed and attempted scans will appear here.'}</p>{!latest && <Link className="button" to="/new-scan">Start a new scan</Link>}</div>}
    </section>
  </>
}
