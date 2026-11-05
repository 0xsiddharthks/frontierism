import { expect, test } from 'claude-code/testing'

import type { FileSnapshot } from '../types'
import { absolutePath, promptReferences, sessionPaths, statusMark, treeRows, viewPaths } from './model'

const SNAPSHOT: FileSnapshot = {
  root: '/work/repo', cwd: '/work/repo/src',
  paths: ['README.md', 'src/app.ts', 'src/lib/util.ts', 'src/lib.test.ts', 'docs/Read me.md'],
  changes: [{ path: 'src/app.ts', status: ' M' }, { path: 'gone.ts', status: ' D' }],
  total: 5, truncated: false,
}

test('a tree keeps folders before files, collapses descendants, and reveals search matches', () => {
  const rows = treeRows(SNAPSHOT.paths, ['src'])
  expect(rows.map(row => row.path)).toEqual(['docs', 'docs/Read me.md', 'src', 'README.md'])
  expect(treeRows(['src/lib/util.ts', 'src/lib.test.ts'], []).map(row => row.path))
    .toEqual(['src', 'src/lib', 'src/lib/util.ts', 'src/lib.test.ts'])
  expect(treeRows(['src/lib/util.ts'], ['src'], true).map(row => row.path))
    .toEqual(['src', 'src/lib', 'src/lib/util.ts'])
})

test('search filters the chosen view, including deleted paths and session-only files', () => {
  const activity = { '/work/repo/new.ts': 'edited', '/work/repo/src/app.ts': 'read', '/work/repo-other/secret.ts': 'read' } as const
  expect(viewPaths(SNAPSHOT, 'all', activity, 'SRC TS')).toEqual(['src/app.ts', 'src/lib/util.ts', 'src/lib.test.ts'])
  expect(viewPaths(SNAPSHOT, 'changes', activity, 'gone')).toEqual(['gone.ts'])
  expect(viewPaths(SNAPSHOT, 'session', activity, '')).toEqual(['new.ts', 'src/app.ts'])
  expect([...sessionPaths('/work/repo', activity).values()]).toEqual(['edited', 'read'])
})

test('prompt references stay in the correct worktree and quote names containing spaces', () => {
  expect(promptReferences(SNAPSHOT, ['src/app.ts', 'docs/Read me.md']))
    .toBe('@/work/repo/src/app.ts @"/work/repo/docs/Read me.md"')
  expect(absolutePath('/work/repo/src', '../docs/Read me.md')).toBe('/work/repo/docs/Read me.md')
  expect(absolutePath('/elsewhere', '/work/repo/a.ts')).toBe('/work/repo/a.ts')
  expect(promptReferences(SNAPSHOT, ['gone.ts'])).toBe('Deleted file: "/work/repo/gone.ts"')
})

test('Git status distinguishes untracked files, renames, deletions, and conflicts', () => {
  expect(['??', 'R ', ' D', 'A ', 'UU', 'AA', 'MM', undefined].map(statusMark))
    .toEqual(['U', 'R', 'D', 'A', '!', '!', 'M', ''])
})
