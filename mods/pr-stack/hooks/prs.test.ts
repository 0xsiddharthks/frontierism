import { expect, test } from 'claude-code/testing'

import { LISTED } from './fixture'
import { ciColor, ciLine, toRows } from './prs'

test('a stack is listed base first, each dependent one level deeper', () => {
  const rows = toRows(JSON.stringify(LISTED))
  expect(rows.map(row => [row.number, row.depth])).toEqual([[1, 0], [2, 1], [3, 2], [4, 0]])
})

test('checks are tallied and reviews named', () => {
  const [tools, bucket, driver, alone] = toRows(JSON.stringify(LISTED))
  expect(tools).toMatchObject({ passing: 2, pending: 0, failing: [], review: 'approved' })
  expect(bucket).toMatchObject({ passing: 0, pending: 2, failing: [], review: 'review required' })
  expect(driver).toMatchObject({ passing: 1, pending: 0, failing: ['test', 'clippy'], review: 'no review', isDraft: true })
  expect(alone).toMatchObject({ passing: 0, pending: 0, failing: [], review: 'changes requested' })
  expect([tools, bucket, driver, alone].map(row => [ciLine(row!), ciColor(row!)])).toEqual([
    ['✓ 2', 'green'], ['● 2', 'yellow'], ['✗ 2  ✓ 1', 'red'], ['no checks', undefined],
  ])
})

test('bases that point at each other still show every PR once', () => {
  const loop = [
    { ...LISTED[0], number: 7, headRefName: 'x', baseRefName: 'y' },
    { ...LISTED[0], number: 8, headRefName: 'y', baseRefName: 'x' },
  ]
  expect(toRows(JSON.stringify(loop)).map(row => row.number)).toEqual([7, 8])
})
