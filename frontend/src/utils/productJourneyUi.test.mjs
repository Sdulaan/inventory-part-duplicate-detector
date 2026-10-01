import assert from 'node:assert/strict'
import test from 'node:test'

import { scanJobOutcome, scanJobProgressLabel } from './productJourneyUi.js'

test('queued and running jobs keep polling', () => {
  assert.deepEqual(scanJobOutcome({ status: 'QUEUED' }), { kind: 'pending' })
  assert.deepEqual(scanJobOutcome({ status: 'RUNNING', stage: 'DISCOVERY' }), { kind: 'pending' })
})

test('a completed job opens its scan only with a valid scan id', () => {
  assert.deepEqual(
    scanJobOutcome({ status: 'COMPLETED', result: { scan_id: 12 } }),
    { kind: 'completed', scanId: 12 },
  )
  assert.deepEqual(
    scanJobOutcome({ status: 'COMPLETED', result: { scan_id: 0 } }),
    { kind: 'failed', status: 'unexpected' },
  )
})

test('a failed job reports the server status for the existing error copy', () => {
  assert.deepEqual(
    scanJobOutcome({ status: 'FAILED', error: { status_code: 422 } }),
    { kind: 'failed', status: 422 },
  )
  assert.deepEqual(scanJobOutcome({ status: 'FAILED' }), { kind: 'failed', status: 500 })
  assert.deepEqual(scanJobOutcome(null), { kind: 'failed', status: 'unexpected' })
})

test('progress labels name the stage in plain words', () => {
  assert.equal(scanJobProgressLabel({ status: 'QUEUED' }), 'Waiting for another scan to finish')
  assert.equal(scanJobProgressLabel({ status: 'RUNNING', stage: 'GROUP_RESOLUTION' }), 'Building duplicate groups')
  assert.equal(scanJobProgressLabel({ status: 'RUNNING', stage: null }), 'Starting scan')
  assert.equal(scanJobProgressLabel({ status: 'RUNNING', stage: 'SOMETHING_NEW' }), 'Starting scan')
})

test('a cancelled job stops polling and is reported as cancelled', () => {
  assert.deepEqual(scanJobOutcome({ status: 'CANCELLED' }), { kind: 'cancelled' })
  assert.equal(scanJobProgressLabel({ status: 'CANCELLED' }), 'Scan cancelled')
  assert.equal(
    scanJobProgressLabel({ status: 'RUNNING', stage: 'DISCOVERY', cancel_requested: true }),
    'Cancelling — the scan stops at its next safe point',
  )
})

test('cancelled scans have their own label and style', async () => {
  const { isScanProcessing, scanStatusKind, scanStatusLabel } = await import('./productJourneyUi.js')
  assert.equal(scanStatusLabel('CANCELLED'), 'Cancelled')
  assert.equal(scanStatusKind('CANCELLED'), 'cancelled')
  assert.equal(isScanProcessing('RUNNING'), true)
  assert.equal(isScanProcessing('CANCELLED'), false)
})
