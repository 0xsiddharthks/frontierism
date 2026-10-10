import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, Timer } from 'claude-code'

import type { Board } from '../types'
import { FIELDS, ciColor, ciLine, toRows } from './prs'

const PANE = 'pr-stack'
const EVERY_MS = 60_000
// How long GitHub takes to show a push or a PR change.
const SETTLE_MS = 5_000
const PR_CHANGE = /\bgit\s+push\b|\bgh\s+pr\s+(create|merge|ready|edit|close|reopen)\b/

const board = atom({ plugin: 'pr-stack', key: 'board' } as const, null)

async function refresh($: EngineInterface): Promise<void> {
  const fetchedAt = await $.clock.now()
  let next: Board
  try {
    const [listed, branch] = await Promise.all([
      $.process.run(
        ['gh', 'pr', 'list', '--author', '@me', '--state', 'open', '--limit', '50', '--json', FIELDS],
        { timeoutMs: 20_000 },
      ),
      $.process.run(['git', 'branch', '--show-current']),
    ])
    next =
      listed.exitCode === 0
        ? { prs: toRows(listed.stdout), branch: branch.stdout.trim(), fetchedAt }
        : { prs: [], branch: '', fetchedAt, error: listed.stderr.trim() || 'gh pr list failed' }
  } catch (error) {
    next = { prs: [], branch: '', fetchedAt, error: String(error) }
  }
  // A failed refresh keeps the last rows on screen under its error.
  await update($, board, last =>
    next.error !== undefined && last !== null ? { ...last, fetchedAt, error: next.error } : next,
  )
}

const isOpen = async ($: EngineInterface): Promise<boolean> =>
  (await $.ui.panes()).some(pane => pane.id === PANE)

const clock = (ms: number): string => {
  const at = new Date(ms)
  return `${String(at.getHours()).padStart(2, '0')}:${String(at.getMinutes()).padStart(2, '0')}`
}

// Set while the pane is open; a reload drops it with the timer it names.
let timer: Timer | undefined

function poll($: EngineInterface): Promise<void> {
  timer?.cancel()
  timer = $.clock.every(EVERY_MS, () => void refresh($))
  return refresh($)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'prs',
      description: 'Show my open PRs in this repo as stacks, with CI and review state',
    })
    // A reload finds the pane still up with no timer behind it.
    if (await isOpen($)) void poll($)
    return next(e)
  })

  on('command.run', { command: 'prs' }, async $ => {
    const opened = await $.ui.open({ id: PANE, title: 'PRs', columns: 64 })
    await poll($)
    return { text: opened.isPlaced ? 'PR stack pane opened.' : 'PR stack pane is open; widen the terminal to see it.' }
  })

  on('ui.close', { id: PANE }, async ($, e, next) => {
    const closed = await next(e)
    if (!(await isOpen($))) {
      timer?.cancel()
      timer = undefined
    }
    return closed
  })

  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const ran = await next(e)
    if (timer !== undefined && PR_CHANGE.test(e.command)) $.clock.after(SETTLE_MS, () => void refresh($))
    return ran
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Link, Text } = $.ui.resolve(e)
    const data = await read($, board)
    if (data === null) return <Text dimColor>Loading your PRs…</Text>

    return (
      <Box flexDirection="column">
        <Box justifyContent="space-between">
          <Text dimColor>
            {data.prs.length} open · {clock(data.fetchedAt)}
          </Text>
          <Button key="refresh" label="refresh" hotkey="r" plain dimColor onPress={() => refresh($)} />
        </Box>
        {data.error !== undefined && <Text color="red" wrap="truncate-end">{data.error}</Text>}
        {data.prs.length === 0 && data.error === undefined && <Text dimColor>No open PRs of yours here.</Text>}
        {data.prs.map(pr => {
          const indent = '  '.repeat(pr.depth)
          const isHere = pr.head === data.branch
          return (
            <Box flexDirection="column" marginTop={pr.depth === 0 ? 1 : 0}>
              <Box>
                <Text dimColor>{pr.depth === 0 ? '' : `${indent.slice(2)}└ `}</Text>
                <Link href={pr.url} label={`#${pr.number}`} />
                <Text bold={isHere} wrap="truncate-end">
                  {' '}
                  {pr.title}
                  {isHere ? ' ◀' : ''}
                </Text>
              </Box>
              <Box>
                <Text>{indent}  </Text>
                <Text {...(ciColor(pr) === undefined ? { dimColor: true } : { color: ciColor(pr) })}>{ciLine(pr)}</Text>
                <Text dimColor>
                  {'  '}
                  {pr.isDraft ? 'draft · ' : ''}
                  {pr.review}
                </Text>
              </Box>
              {pr.failing.length > 0 && (
                <Text color="red" wrap="truncate-end">
                  {indent}  {pr.failing.slice(0, 3).join(', ')}
                  {pr.failing.length > 3 ? ` +${pr.failing.length - 3}` : ''}
                </Text>
              )}
            </Box>
          )
        })}
      </Box>
    )
  })
}
