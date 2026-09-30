const STATUS_LABELS = {
  COMPLETED: 'Completed',
  RUNNING: 'Processing',
  PROCESSING: 'Processing',
  FAILED: 'Failed',
  VALIDATION_ONLY: 'Validation complete — not yet scanned',
}

export function scanStatusLabel(status) {
  const value = String(status || '').trim().toUpperCase()
  return STATUS_LABELS[value] || 'Status unavailable'
}

export function scanStatusKind(status) {
  const value = String(status || '').trim().toUpperCase()
  if (value === 'COMPLETED') return 'complete'
  if (value === 'RUNNING' || value === 'PROCESSING') return 'processing'
  if (value === 'FAILED') return 'failed'
  return 'neutral'
}

export function orderScans(scans = []) {
  return [...scans].sort((left, right) => {
    const leftTime = Date.parse(left?.started_at || left?.completed_at || '') || 0
    const rightTime = Date.parse(right?.started_at || right?.completed_at || '') || 0
    return rightTime - leftTime || Number(right?.id || 0) - Number(left?.id || 0)
  })
}

export function formatScanTime(value) {
  if (!value) return 'Time unavailable'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Time unavailable'
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium', timeStyle: 'short',
  }).format(date)
}

export function validationContextKey(fileGeneration, selected, mapping, scope) {
  const { partType = '', includeInventoryParts = true } = scope && typeof scope === 'object' ? scope : {}
  const orderedMapping = Object.fromEntries(
    Object.entries(mapping || {}).sort(([left], [right]) => left.localeCompare(right)),
  )
  return JSON.stringify({
    file_generation: Number(fileGeneration) || 0,
    selected_fields: [...(selected || [])].sort(),
    column_mapping: orderedMapping,
    part_type: partType,
    include_inventory_parts: includeInventoryParts,
  })
}

export function formatElapsed(totalSeconds) {
  const seconds = Math.max(0, Math.floor(Number(totalSeconds) || 0))
  const minutes = Math.floor(seconds / 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
}

export function processingGuidance(elapsedSeconds) {
  if (Number(elapsedSeconds) >= 60) {
    return 'The scan is still running on the server. Large inventories can take many minutes. Do not resubmit; if you leave this page, the finished scan appears under Recent scans.'
  }
  return 'Large inventories can take several minutes. Keep this page open to open the result as soon as it is ready.'
}

const SCAN_STAGE_LABELS = {
  CANONICAL_CATALOG: 'Reading records',
  DISCOVERY: 'Finding candidate matches',
  SIGNED_EVIDENCE: 'Checking match evidence',
  GROUP_RESOLUTION: 'Building duplicate groups',
  G2_V2_PROJECTION: 'Preparing results',
}

export function scanJobProgressLabel(job) {
  const status = String(job?.status || '').toUpperCase()
  if (status === 'QUEUED') return 'Waiting for another scan to finish'
  if (status === 'COMPLETED') return 'Opening results'
  return SCAN_STAGE_LABELS[String(job?.stage || '').toUpperCase()] || 'Starting scan'
}

/**
 * Decide what the page does with one poll of a background scan job:
 * keep polling, open the finished scan, or show an error.
 */
export function scanJobOutcome(job) {
  const status = String(job?.status || '').toUpperCase()
  if (status === 'QUEUED' || status === 'RUNNING') return { kind: 'pending' }
  if (status === 'COMPLETED') {
    const scanId = Number(job?.result?.scan_id)
    return Number.isInteger(scanId) && scanId > 0
      ? { kind: 'completed', scanId }
      : { kind: 'failed', status: 'unexpected' }
  }
  if (status === 'FAILED') return { kind: 'failed', status: job?.error?.status_code ?? 500 }
  return { kind: 'failed', status: 'unexpected' }
}

export function scanRequestError(status, phase = 'scan') {
  const validating = phase === 'validation'
  if (Number(status) === 422) return {
    title: validating ? 'Validation failed' : 'Scan could not start',
    message: 'The CSV or field mapping was rejected. Check the required columns, update the mapping if needed, and validate again.',
  }
  if (Number(status) >= 500) return {
    title: validating ? 'Validation service error' : 'Scan failed',
    message: validating
      ? 'The server could not validate this file. Your local selection remains available; try validation again.'
      : 'The server could not complete the request. A completed result is not known. Check Recent scans before safely trying again.',
  }
  if (status == null) return {
    title: 'Connection interrupted',
    message: validating
      ? 'Validation did not complete. Check that the backend is running, then try validation again.'
      : 'The request response was interrupted. Do not assume a result exists; check Recent scans before trying again.',
  }
  return {
    title: validating ? 'File could not be validated' : 'Unexpected scan response',
    message: validating
      ? 'Use a supported CSV with the required columns, review the mapping, and try validation again.'
      : 'The scan result could not be confirmed. Check Recent scans before trying again.',
  }
}
