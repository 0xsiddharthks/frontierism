import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'

import { LISTED } from './fixture'

const PANE = {
  component: 'Pane',
  requestId: 'pr-stack',
  props: { title: 'PRs', isFocused: false, bodyColumns: 64, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
} as const

// `/prs` as the person types it at the prompt.
const PRS = {
  command: 'prs',
  args: '',
  origin: { kind: 'composer' },
  presentation: { isFullscreen: true, columns: 200 },
} as const

// The world beneath the mod: what `gh` and `git` print, and a pane that opens.
function world(on: On, gh: { exitCode: number; stdout: string; stderr: string }) {
  const seen = { fetches: 0 }
  const clock = mock.clock(on, { now: 1_790_000_000_000 })
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.panes', () => ({ value: [{ id: 'pr-stack', title: 'PRs', isShown: true, isFocused: false, isPlaced: true }] }))
  on('process.run', ($, e) => {
    if (e.argv[0] === 'gh') seen.fetches += 1
    const ran = e.argv[0] === 'gh' ? gh : { exitCode: 0, stdout: 'b\n', stderr: '' }
    return { value: { ...ran, isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('tool.call', { tool: 'Bash' }, () => ({ result: { stdout: '', stderr: '', interrupted: false } }))
  return { seen, clock }
}

test('/prs draws the stacks on every surface and marks the branch you are on', async ($, on) => {
  world(on, { exitCode: 0, stdout: JSON.stringify(LISTED), stderr: '' })
  expect(await $.command.run(PRS)).toMatchObject({ text: 'PR stack pane opened.' })
  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ plugin: 'pr-stack', surface, ...PANE })
    expect(await ui.find({ type: 'Text', text: '4 open' })).toBeDefined()
    expect(await ui.find({ type: 'Link', text: '#2' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: 'bucket ◀' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: 'tools ◀' })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: 'test, clippy' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: 'draft · no review' })).toBeDefined()
    await ui.unmount()
  }
})

test('the pane refreshes on its button, on the timer, and after a push', async ($, on) => {
  const { seen, clock } = world(on, { exitCode: 0, stdout: '[]', stderr: '' })
  await $.command.run(PRS)
  expect(seen.fetches).toBe(1)
  const ui = await $.ui.mount({ plugin: 'pr-stack', surface: 'terminal', ...PANE })
  expect(await ui.find({ type: 'Text', text: 'No open PRs of yours here.' })).toBeDefined()
  await ui.press({ key: 'refresh' })
  expect(seen.fetches).toBe(2)
  await clock.advance(60_000)
  expect(seen.fetches).toBe(3)
  await $.tool.call({ tool: 'Bash', command: 'git status' })
  await $.tool.call({ tool: 'Bash', command: 'git push -u origin HEAD' })
  await clock.advance(5_000)
  expect(seen.fetches).toBe(4)
})

test('a failed fetch shows its error', async ($, on) => {
  world(on, { exitCode: 1, stdout: '', stderr: 'gh: not logged in' })
  await $.command.run(PRS)
  const ui = await $.ui.mount({ plugin: 'pr-stack', surface: 'terminal', ...PANE })
  expect(await ui.find({ type: 'Text', text: 'gh: not logged in' })).toBeDefined()
})
