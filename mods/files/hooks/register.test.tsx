import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'

import type { FileSnapshot } from '../types'

const PANE = {
  component: 'Pane', requestId: 'files',
  props: { title: 'Files', isFocused: true, bodyColumns: 80, placement: 'dock', scroll: { offset: 0, bodyRows: 40 }, view: {} },
} as const
const COMMAND = {
  command: 'files', args: '', origin: { kind: 'composer' },
  presentation: { isFullscreen: true, columns: 200 },
} as const
const SNAPSHOT: FileSnapshot = {
  root: '/work/repo', cwd: '/work/repo', paths: ['README.md', 'src/app.ts', 'docs/Read me.md', 'gone.ts'],
  changes: [{ path: 'src/app.ts', status: ' M' }, { path: 'gone.ts', status: ' D' }], total: 4, truncated: false,
}

function world(on: On, snapshot = SNAPSHOT) {
  const seen = { scans: 0, previews: [] as string[], draft: 'Please review', submitted: 0, opened: false,
    canFill: true, error: '', root: SNAPSHOT.root, failRead: false }
  const clock = mock.clock(on, { now: 1_790_000_000_000 })
  on('session.cwd', () => ({ value: '/work/repo' }))
  on('ui.open', () => { seen.opened = true; return { value: { isPlaced: true } } })
  on('ui.close', () => { seen.opened = false; return { value: undefined } })
  on('ui.panes', () => ({ value: seen.opened ? [{ id: 'files', title: 'Files', isShown: true, isFocused: true, isPlaced: true }] : [] }))
  on('process.run', ($, e) => {
    const request = JSON.parse(e.argv[2]!) as { op: string; path?: string; mode?: string }
    if (request.op === 'scan') seen.scans += 1
    else seen.previews.push(`${request.mode}:${request.path}`)
    const answer = seen.error !== '' ? { error: seen.error } : request.op === 'scan'
      ? { ...snapshot, root: seen.root }
      : { kind: request.mode, source: request.mode === 'diff' ? '-old\n+new' : 'export const app = true;\n\u001b[31m', note: '' }
    return { value: { exitCode: 0, stdout: JSON.stringify(answer), stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('prompt.read', () => ({ value: { text: seen.draft, cursor: seen.draft.length } }))
  on('prompt.fill', ($, e) => {
    if (seen.canFill) seen.draft = e.mode === 'append' ? seen.draft + e.text : e.text
    return { isFilled: seen.canFill, text: seen.draft, cursor: seen.draft.length }
  })
  on('prompt.submit', () => { seen.submitted += 1; return { drop: 'No model turns in tests.' } })
  // Tools answer through the same middleware as real successful or failed calls.
  on('tool.call', ($, e) => e.tool === 'Read' && seen.failRead
    ? { isError: true, result: 'missing file', text: 'missing file' } : { result: {} })
  return { seen, clock }
}

test('/files draws its controls on all surfaces, expands folders, and searches as you type', async ($, on) => {
  world(on)
  expect(await $.command.run(COMMAND)).toMatchObject({ text: 'Files pane opened.' })
  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ plugin: 'files', surface, ...PANE })
    expect(await ui.find({ key: 'view-all' })).toBeDefined()
    expect(await ui.find({ key: 'view-changes' })).toBeDefined()
    expect(await ui.find({ key: 'view-session' })).toBeDefined()
    await ui.press({ key: 'collapse' })
    expect(await ui.find({ key: 'open:src/app.ts' })).toBeUndefined()
    await ui.press({ key: 'open:src' })
    expect(await ui.find({ key: 'open:src/app.ts' })).toBeDefined()
    await ui.input({ key: 'search', text: 'read ME', kind: 'change' })
    expect(await ui.find({ key: 'open:README.md' })).toBeDefined()
    expect(await ui.find({ key: 'open:src/app.ts' })).toBeUndefined()
    await ui.input({ key: 'search', text: '', kind: 'change' })
    await ui.unmount()
  }
})

test('Git changes preview a diff, content can be opened, and binary/control text cannot break drawing', async ($, on) => {
  const { seen } = world(on)
  await $.command.run(COMMAND)
  const ui = await $.ui.mount({ plugin: 'files', surface: 'terminal', ...PANE })
  await ui.press({ key: 'view-changes' })
  expect(await ui.find({ key: 'open:README.md' })).toBeUndefined()
  expect(await ui.find({ key: 'open:gone.ts' })).toBeDefined()
  await ui.press({ key: 'open:src/app.ts' })
  expect(seen.previews).toEqual(['diff:src/app.ts'])
  expect(await ui.find({ type: 'Code', text: '+new' })).toBeDefined()
  await ui.press({ key: 'preview-content' })
  expect(await ui.find({ type: 'Code', text: 'export const app' })).toBeDefined()
  expect(await ui.find({ type: 'Code', text: '\\u001b[31m' })).toBeDefined()
  await ui.press({ key: 'preview-close' })
  expect(await ui.find({ type: 'Code' })).toBeUndefined()
})

test('selection persists through search and views, appends references, and never submits the draft', async ($, on) => {
  const { seen } = world(on)
  await $.command.run(COMMAND)
  const ui = await $.ui.mount({ plugin: 'files', surface: 'terminal', ...PANE })
  await ui.press({ key: 'select:README.md' })
  await ui.input({ key: 'search', text: 'Read me.md' })
  await ui.press({ key: 'select:docs/Read me.md' })
  await ui.press({ key: 'view-session' })
  await ui.press({ key: 'add-to-prompt' })
  expect(seen.draft).toBe('Please review @/work/repo/README.md @"/work/repo/docs/Read me.md" ')
  expect(seen.submitted).toBe(0)
  seen.canFill = false
  await ui.press({ key: 'add-to-prompt' })
  expect(await ui.find({ type: 'Text', text: 'could not take' })).toBeDefined()
  await ui.press({ key: 'clear-selection' })
  expect(await ui.find({ key: 'add-to-prompt' })).toBeUndefined()
})

test('session activity records successful file calls while closed and keeps edited markers after reads', async ($, on) => {
  const { seen } = world(on)
  await $.tool.call({ tool: 'Read', file_path: '/work/repo/README.md' })
  await $.tool.call({ tool: 'Edit', file_path: '/work/repo/src/app.ts', old_string: 'old', new_string: 'new' })
  await $.tool.call({ tool: 'Read', file_path: 'src/app.ts' })
  seen.failRead = true
  await $.tool.call({ tool: 'Read', file_path: '/work/repo/missing.ts' })
  expect(seen.scans).toBe(0)
  await $.command.run(COMMAND)
  const ui = await $.ui.mount({ plugin: 'files', surface: 'terminal', ...PANE })
  await ui.press({ key: 'view-session' })
  expect((await ui.find({ key: 'open:README.md' }))?.text).toContain('· read')
  expect((await ui.find({ key: 'open:src/app.ts' }))?.text).toContain('· edited')
  expect(await ui.find({ key: 'open:missing.ts' })).toBeUndefined()
  expect(await ui.find({ key: 'open:gone.ts' })).toBeUndefined()
})

test('refresh runs after tools and on the timer, keeps the last listing on errors, and stops when closed', async ($, on) => {
  const { seen, clock } = world(on)
  await $.command.run(COMMAND)
  const ui = await $.ui.mount({ plugin: 'files', surface: 'terminal', ...PANE })
  await $.tool.call({ tool: 'Bash', command: 'git status' })
  await clock.advance(250)
  expect(seen.scans).toBe(2)
  seen.error = 'Temporary Git error'
  await clock.advance(10_000)
  expect(await ui.find({ type: 'Text', text: 'Temporary Git error' })).toBeDefined()
  expect(await ui.find({ key: 'open:README.md' })).toBeDefined()
  const beforeClose = seen.scans
  await ui.press({ key: 'close-pane' })
  expect(seen.opened).toBe(false)
  await clock.advance(30_000)
  expect(seen.scans).toBe(beforeClose)
})

test('moving to a different working tree clears selections and previews', async ($, on) => {
  const { seen } = world(on)
  await $.command.run(COMMAND)
  const ui = await $.ui.mount({ plugin: 'files', surface: 'terminal', ...PANE })
  await ui.press({ key: 'select:README.md' })
  await ui.press({ key: 'open:README.md' })
  seen.root = '/work/another-worktree'
  await ui.press({ key: 'refresh' })
  expect(await ui.find({ key: 'add-to-prompt' })).toBeUndefined()
  expect(await ui.find({ type: 'Code' })).toBeUndefined()
})

test('file and preview pages stay usable in a short pane, including unusual file names', async ($, on) => {
  const paths = ['a\nb.ts', ...Array.from({ length: 25 }, (_, index) => `file-${index}.ts`)]
  world(on, { ...SNAPSHOT, paths, changes: [], total: paths.length })
  await $.command.run(COMMAND)
  const ui = await $.ui.mount({ plugin: 'files', surface: 'terminal', ...PANE,
    props: { ...PANE.props, scroll: { offset: 0, bodyRows: 24 } } })
  expect(await ui.find({ key: 'next' })).toBeDefined()
  expect((await ui.find({ key: 'open:a\nb.ts' }))?.text).toContain('a\\u000ab.ts')
  await ui.press({ key: 'open:a\nb.ts' })
  expect(await ui.find({ type: 'Code', text: 'export const' })).toBeDefined()
  await ui.press({ key: 'next' })
  expect(await ui.find({ key: 'previous' })).toBeDefined()
})
