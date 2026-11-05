import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, Timer } from 'claude-code'

import type { Activity, FileSnapshot, Preview, PreviewMode, View } from '../types'
import { absolutePath, directories, displayPath, initialState, language, promptReferences, sessionPaths, statusMark, treeRows, viewPaths } from './model'

const PANE = 'files'
const browser = atom({ plugin: 'files', key: 'browser' } as const, initialState())
const EVERY_MS = 10_000
let timer: Timer | undefined
let pending: Timer | undefined
let scanVersion = 0
let previewVersion = 0

async function backend<T>($: EngineInterface, request: Record<string, unknown>): Promise<T> {
  const result = await $.process.run(['python3', `${$.plugin.root}/hooks/files.py`, JSON.stringify(request)], { timeoutMs: 25_000 })
  if (result.exitCode !== 0) throw new Error(result.stderr.trim() || 'Could not run the file browser. It needs Python 3 and Git.')
  if (result.isStdoutTruncated) throw new Error('The file listing was too large. Try a smaller working tree.')
  const answer = JSON.parse(result.stdout) as T & { error?: string }
  if (answer.error !== undefined) throw new Error(answer.error)
  return answer
}

async function preview($: EngineInterface, path: string, mode: PreviewMode, reset = true): Promise<void> {
  const version = reset ? ++previewVersion : previewVersion
  const current = await read($, browser)
  const { snapshot } = current
  if (snapshot === null) return
  if (!reset && (current.active !== path || current.mode !== mode)) return
  if (reset) await update($, browser, state => ({ ...state, active: path, mode, preview: null, previewPage: 0 }))
  let next: Preview
  try {
    next = await backend<Preview>($, { op: 'preview', root: snapshot.root, path, mode })
  } catch (error) {
    next = { kind: mode, source: '', note: String(error) }
  }
  if (version !== previewVersion) return
  await update($, browser, state => state.snapshot?.root === snapshot.root && state.active === path && state.mode === mode
    ? { ...state, preview: next } : state)
}

async function refresh($: EngineInterface): Promise<void> {
  const version = ++scanVersion
  try {
    // session.repo().root names the main checkout even in a worktree. Let Git
    // locate the current working tree from cwd instead.
    const snapshot = await backend<FileSnapshot>($, { op: 'scan', cwd: await $.session.cwd() })
    if (version !== scanVersion) return
    await update($, browser, state => {
      const moved = state.snapshot?.root !== snapshot.root
      return { ...state, snapshot, error: undefined,
        ...(moved ? { selected: [], active: null, preview: null, page: 0,
          collapsed: directories(snapshot.paths).filter(path => !path.includes('/')) } : {}) }
    })
    const state = await read($, browser)
    if (state.active !== null) await preview($, state.active, state.mode, false)
  } catch (error) {
    if (version === scanVersion) await update($, browser, state => ({ ...state, error: String(error) }))
  }
}

const isOpen = async ($: EngineInterface): Promise<boolean> => (await $.ui.panes()).some(pane => pane.id === PANE)

function poll($: EngineInterface): Promise<void> {
  timer?.cancel()
  timer = $.clock.every(EVERY_MS, () => void refresh($))
  return refresh($)
}

function schedule($: EngineInterface): void {
  if (timer === undefined) return
  pending?.cancel()
  pending = $.clock.after(250, () => void refresh($))
}

async function stopIfClosed($: EngineInterface): Promise<void> {
  if (await isOpen($)) return
  timer?.cancel()
  pending?.cancel()
  timer = undefined
  pending = undefined
  ++scanVersion
  ++previewVersion
}

async function closePane($: EngineInterface): Promise<void> {
  await $.ui.close({ id: PANE })
  // A mod's own API calls bypass its matching operation hooks.
  await stopIfClosed($)
}

async function setView($: EngineInterface, view: View): Promise<void> {
  await update($, browser, state => ({ ...state, view, page: 0,
    collapsed: view === 'all' && state.snapshot !== null
      ? directories(state.snapshot.paths).filter(path => !path.includes('/')) : [] }))
}

async function search($: EngineInterface, query: string): Promise<void> {
  await update($, browser, state => ({ ...state, query, page: 0 }))
}

async function select($: EngineInterface, path: string): Promise<void> {
  await update($, browser, state => ({ ...state, notice: undefined,
    selected: state.selected.includes(path) ? state.selected.filter(item => item !== path) : [...state.selected, path] }))
}

async function addToPrompt($: EngineInterface): Promise<void> {
  const state = await read($, browser)
  if (state.snapshot === null || state.selected.length === 0) return
  const { text } = await $.prompt.read()
  const refs = promptReferences(state.snapshot, state.selected)
  const result = await $.prompt.fill({ text: `${text !== '' && !/\s$/.test(text) ? ' ' : ''}${refs} `, mode: 'append' })
  await update($, browser, current => ({ ...current, notice: result.isFilled
    ? `Added ${state.selected.length} file reference${state.selected.length === 1 ? '' : 's'} to your draft.`
    : 'The prompt could not take the references. Return to the prompt and try again.' }))
}

// Code accepts only tabs and newlines as controls. Escape other controls in a
// preview so arbitrary file bytes cannot refuse the whole pane's drawing.
const sourceText = (text: string): string => text.replace(/[\x00-\x08\x0b-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]/g, displayPath)

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'files', description: 'Browse files, Git changes, and session activity', argumentHint: '[search]' })
    if (await isOpen($)) void poll($)
    return next(e)
  })

  on('command.run', { command: 'files' }, async ($, e) => {
    if (e.args.trim() !== '') {
      await setView($, 'all')
      await search($, e.args.trim())
    }
    const opened = await $.ui.open({ id: PANE, title: 'Files', columns: 80, rows: 32, focus: true })
    await poll($)
    return { text: opened.isPlaced ? 'Files pane opened.' : 'Files pane is open; widen the terminal to see it.' }
  })

  on('ui.close', { id: PANE }, async ($, e, next) => {
    const closed = await next(e)
    await stopIfClosed($)
    return closed
  })

  on('tool.call', async ($, e, next) => {
    const result = await next(e)
    if (result.isError || result.deny !== undefined) return result
    const path = e.tool === 'Read' || e.tool === 'Edit' || e.tool === 'Write' ? e.file_path
      : e.tool === 'NotebookEdit' ? e.notebook_path : undefined
    if (path !== undefined) {
      const absolute = absolutePath(await $.session.cwd(), path)
      const kind: Activity = e.tool === 'Read' ? 'read' : 'edited'
      await update($, browser, state => {
        const activity = { ...state.activity }
        activity[absolute] = kind === 'read' && activity[absolute] !== 'edited' ? 'read' : 'edited'
        return { ...state, activity }
      })
    }
    if (path !== undefined || e.tool === 'Bash') schedule($)
    return result
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    schedule($)
    return result
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Code, Input, Text } = $.ui.resolve(e)
    const state = await read($, browser)
    const { snapshot } = state
    if (snapshot === null) return (
      <Box flexDirection="column">
        <Text>{state.error === undefined ? 'Loading files…' : displayPath(state.error)}</Text>
        <Button key="refresh" label="Retry" onPress={() => refresh($)} />
      </Box>
    )
    const paths = viewPaths(snapshot, state.view, state.activity, state.query)
    const rows = treeRows(paths, state.collapsed, state.query.trim() !== '')
    const selected = new Set(state.selected)
    const activity = sessionPaths(snapshot.root, state.activity)
    const changes = new Map(snapshot.changes.map(item => [item.path, item.status]))
    const height = e.props.scroll.bodyRows
    const pageSize = Math.max(4, Math.min(14, height - (state.active === null ? 12 : 23)))
    const pages = Math.max(1, Math.ceil(rows.length / pageSize))
    const page = Math.min(state.page, pages - 1)
    const visible = rows.slice(page * pageSize, (page + 1) * pageSize)
    const previewLines = Math.max(4, Math.min(12, height - pageSize - 17))
    const lines = state.preview?.source.split('\n') ?? []
    const previewPages = Math.max(1, Math.ceil(lines.length / previewLines))
    const previewPage = Math.min(state.previewPage, previewPages - 1)
    const previewStart = previewPage * previewLines

    return (
      <Box flexDirection="column">
        <Text bold wrap="truncate-end">{displayPath(snapshot.root)}</Text>
        <Box gap={1}>
          <Button key="view-all" label="All files" hotkey="a" plain dimColor={state.view !== 'all'} onPress={() => setView($, 'all')} />
          <Button key="view-changes" label="Git changes" hotkey="g" plain dimColor={state.view !== 'changes'} onPress={() => setView($, 'changes')} />
          <Button key="view-session" label="This session" hotkey="s" plain dimColor={state.view !== 'session'} onPress={() => setView($, 'session')} />
        </Box>
        <Input key="search" label="Search" placeholder="File name or path" value={state.query} submitLabel="filter"
          onInput={value => search($, value)} onSubmit={value => search($, value)} />
        <Box justifyContent="space-between">
          <Text dimColor>{paths.length} files · {state.selected.length} selected</Text>
          <Box gap={1}>
            <Button key="expand" label="Expand" plain dimColor onPress={() => update($, browser, current => ({ ...current, collapsed: [], page: 0 }))} />
            <Button key="collapse" label="Collapse" plain dimColor onPress={() => update($, browser, current => ({ ...current, collapsed: directories(paths), page: 0 }))} />
            <Button key="refresh" label="Refresh" hotkey="r" plain dimColor onPress={() => refresh($)} />
            <Button key="close-pane" label="Close" plain dimColor onPress={() => closePane($)} />
          </Box>
        </Box>
        {state.error !== undefined && <Text color="red" wrap="truncate-end">{displayPath(state.error)}</Text>}
        {snapshot.truncated && <Text color="yellow">Loaded {snapshot.paths.length} of {snapshot.total} files; search covers loaded files.</Text>}
        {state.view === 'session' && <Text dimColor>Recorded reads and edits · shell-only changes are in Git changes</Text>}
        {rows.length === 0 && <Text dimColor>{state.query.trim() !== '' ? 'No matching files.'
          : state.view === 'changes' ? 'No uncommitted Git changes.'
            : state.view === 'session' ? 'No file reads or edits recorded yet.' : 'No files in this working tree.'}</Text>}
        {visible.map(row => {
          const indent = '  '.repeat(Math.min(row.depth, 10))
          const badge = statusMark(changes.get(row.path))
          const touched = activity.get(row.path)
          return (
            <Box>
              {!row.folder && <Button key={`select:${row.path}`} label={selected.has(row.path) ? '[x]' : '[ ]'} plain onPress={() => select($, row.path)} />}
              <Button key={`open:${row.path}`} plain
                label={`${row.folder ? '' : ' '}${indent}${row.folder ? `${state.collapsed.includes(row.path) && state.query.trim() === '' ? '▸' : '▾'} ` : state.active === row.path ? '› ' : ''}${displayPath(row.name)}${row.folder ? '/' : ''}${badge ? `  ${badge}` : ''}${touched ? ` · ${touched}` : ''}`}
                onPress={() => row.folder
                  ? update($, browser, current => ({ ...current, collapsed: current.collapsed.includes(row.path)
                    ? current.collapsed.filter(path => path !== row.path) : [...current.collapsed, row.path], page: 0 }))
                  : preview($, row.path, changes.has(row.path) ? 'diff' : 'content')} />
            </Box>
          )
        })}
        {pages > 1 && <Box gap={1}>
          {page > 0 && <Button key="previous" label="Previous files" plain onPress={() => update($, browser, current => ({ ...current, page: page - 1 }))} />}
          <Text dimColor>{page + 1}/{pages}</Text>
          {page + 1 < pages && <Button key="next" label="Next files" plain onPress={() => update($, browser, current => ({ ...current, page: page + 1 }))} />}
        </Box>}
        <Box gap={1} marginTop={1}>
          {state.selected.length > 0 && <Button key="add-to-prompt" label={`Add ${state.selected.length} to prompt`} onPress={() => addToPrompt($)} />}
          {state.selected.length > 0 && <Button key="clear-selection" label="Clear selection" plain dimColor onPress={() => update($, browser, current => ({ ...current, selected: [], notice: undefined }))} />}
          {state.selected.length === 0 && <Text dimColor>[ ] selects a file · its name opens a preview</Text>}
        </Box>
        {state.notice !== undefined && <Text dimColor wrap="truncate-end">{state.notice}</Text>}
        {state.active !== null && <Box flexDirection="column" marginTop={1}>
          <Text bold wrap="truncate-end">{displayPath(state.active)}</Text>
          <Box gap={1}>
            <Button key="preview-content" label="Content" plain dimColor={state.mode !== 'content'} onPress={() => preview($, state.active!, 'content')} />
            <Button key="preview-diff" label="Diff" plain dimColor={state.mode !== 'diff'} onPress={() => preview($, state.active!, 'diff')} />
            <Button key="preview-close" label="Close preview" plain dimColor onPress={() => update($, browser, current => ({ ...current, active: null, preview: null }))} />
          </Box>
          {state.preview === null ? <Text dimColor>Loading preview…</Text> : <Box flexDirection="column">
            {state.preview.note !== '' && <Text dimColor wrap="truncate-end">{displayPath(state.preview.note)}</Text>}
            {state.preview.source === '' ? <Text dimColor>{state.preview.note === '' ? 'Empty file.' : ''}</Text>
              : <Code source={sourceText(lines.slice(previewStart, previewStart + previewLines).join('\n'))}
                language={state.preview.kind === 'diff' ? 'diff' : language(state.active)} path={state.active}
                startLine={previewStart + 1} wrap="truncate-end" />}
            {previewPages > 1 && <Box gap={1}>
              {previewPage > 0 && <Button key="preview-previous" label="Previous lines" plain onPress={() => update($, browser, current => ({ ...current, previewPage: previewPage - 1 }))} />}
              <Text dimColor>Lines {previewStart + 1}–{Math.min(previewStart + previewLines, lines.length)} of {lines.length}</Text>
              {previewPage + 1 < previewPages && <Button key="preview-next" label="Next lines" plain onPress={() => update($, browser, current => ({ ...current, previewPage: previewPage + 1 }))} />}
            </Box>}
          </Box>}
        </Box>}
      </Box>
    )
  })
}
