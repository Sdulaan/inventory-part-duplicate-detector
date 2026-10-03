import assert from 'node:assert/strict'
import test from 'node:test'

import { scanDownloadFilename } from '../src/utils/partTypeUi.js'

test('download filenames use the part type label, date, time, and original extension', () => {
  const now = new Date(2026, 9, 3, 14, 5, 9)
  assert.equal(scanDownloadFilename('INVENTORY', 'scan-1-x.xlsx', now), 'Inventory Parts Scan_2026-10-03_14-05-09.xlsx')
  assert.equal(scanDownloadFilename('PURCHASE', 'scan-1-x.csv', now), 'Purchase Parts Scan_2026-10-03_14-05-09.csv')
  assert.equal(scanDownloadFilename('SALES', 'scan-1-x.csv', now), 'Sales Parts Scan_2026-10-03_14-05-09.csv')
})
