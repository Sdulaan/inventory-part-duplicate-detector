import assert from 'node:assert/strict'
import test from 'node:test'

import {
  DEFAULT_CONDITION_HELP,
  SITE_CONDITION_HELP,
  duplicateConditionHelp,
} from './duplicateConditionSemantics.js'

test('Site alone is presented as a selected must-match condition', () => {
  assert.equal(duplicateConditionHelp('CONTRACT'), SITE_CONDITION_HELP)
  assert.equal(SITE_CONDITION_HELP, 'Must match when selected')
})

test('other duplicate conditions retain discovery and scoring semantics', () => {
  for (const field of ['UNIT_MEAS', 'TYPE_CODE', 'HAZARD_CODE']) {
    assert.equal(duplicateConditionHelp(field), DEFAULT_CONDITION_HELP)
  }
})
