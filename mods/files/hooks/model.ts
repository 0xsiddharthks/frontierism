import type { Activity, FileSnapshot, FilesState, View } from '../types'

export type TreeRow = { path: string; name: string; depth: number; folder: boolean }

export const initialState = (): FilesState => ({
  snapshot: null, view: 'all', query: '', collapsed: [], page: 0,
  selected: [], active: null, mode: 'content', preview: null, previewPage: 0,
  activity: {},
})

// File tools give absolute paths or paths relative to their working directory.
export function absolutePath(cwd: string, path: string): string {
  const joined = path.startsWith('/') ? path : `${cwd}/${path}`
  const parts: string[] = []
  for (const part of joined.split('/')) {
    if (part === '..') parts.pop()
    else if (part !== '' && part !== '.') parts.push(part)
  }
  return `/${parts.join('/')}`
}

export function sessionPaths(root: string, activity: Record<string, Activity>): Map<string, Activity> {
  const prefix = `${root.replace(/\/$/, '')}/`
  return new Map(Object.entries(activity)
    .filter(([path]) => path.startsWith(prefix) && !path.slice(prefix.length).split('/').includes('.git'))
    .map(([path, kind]) => [path.slice(prefix.length), kind]))
}

export function viewPaths(snapshot: FileSnapshot, view: View, activity: Record<string, Activity>, query: string): string[] {
  const paths = view === 'all' ? snapshot.paths
    : view === 'changes' ? snapshot.changes.map(item => item.path)
      : [...sessionPaths(snapshot.root, activity).keys()]
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean)
  return [...new Set(paths)].filter(path => terms.every(term => path.toLowerCase().includes(term)))
}

export function directories(paths: readonly string[]): string[] {
  const folders = new Set<string>()
  for (const path of paths) {
    const parts = path.split('/')
    for (let end = 1; end < parts.length; end++) folders.add(parts.slice(0, end).join('/'))
  }
  return [...folders]
}

export function treeRows(paths: readonly string[], collapsed: readonly string[], searching = false): TreeRow[] {
  const folders = new Set(directories(paths))
  const closed = new Set(searching ? [] : collapsed)
  const rows: TreeRow[] = []
  for (const path of new Set([...folders, ...paths])) {
    const parts = path.split('/')
    if (parts.slice(0, -1).some((_, index) => closed.has(parts.slice(0, index + 1).join('/')))) continue
    rows.push({ path, name: parts[parts.length - 1]!, depth: parts.length - 1, folder: folders.has(path) })
  }
  // Sort by path segments, folders first at every level, rather than comparing
  // full paths (which puts a.txt ahead of the contents of a/).
  return rows.sort((left, right) => {
    const a = left.path.split('/'), b = right.path.split('/')
    for (let index = 0; index < Math.min(a.length, b.length); index++) {
      if (a[index] === b[index]) continue
      const aFolder = index < a.length - 1 || left.folder
      const bFolder = index < b.length - 1 || right.folder
      if (aFolder !== bFolder) return aFolder ? -1 : 1
      return a[index]!.localeCompare(b[index]!, undefined, { numeric: true, sensitivity: 'base' })
    }
    return a.length - b.length || left.path.localeCompare(right.path)
  })
}

export const displayPath = (path: string): string => path.replace(/[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]/g,
  character => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`)

export const statusMark = (status: string | undefined): string => status === undefined ? ''
  : status === '??' ? 'U' : status.includes('U') || status === 'AA' || status === 'DD' ? '!'
    : status.includes('R') ? 'R' : status.includes('D') ? 'D' : status.includes('A') ? 'A' : 'M'

export function promptReferences(snapshot: FileSnapshot, paths: readonly string[]): string {
  // Absolute references stay correct when Claude starts in a repo subdirectory
  // or changes cwd. Quote names containing spaces or punctuation for @ mentions.
  const changes = new Map(snapshot.changes.map(item => [item.path, item.status]))
  return paths.map(path => {
    const full = `${snapshot.root}/${path}`
    // A deleted path cannot be read by @ mention, but is useful context.
    if (changes.get(path)?.includes('D')) return `Deleted file: ${JSON.stringify(full)}`
    return `@${/^[\w./-]+$/.test(full) ? full : JSON.stringify(full)}`
  }).join(' ')
}

export function language(path: string): string {
  const extension = path.split('.').pop()?.toLowerCase() ?? ''
  return ({ ts: 'typescript', tsx: 'tsx', js: 'javascript', jsx: 'jsx', py: 'python', rs: 'rust',
    md: 'markdown', sh: 'bash', zsh: 'bash', yml: 'yaml', toml: 'toml', json: 'json', css: 'css',
    html: 'html', go: 'go', rb: 'ruby', swift: 'swift', sql: 'sql', yaml: 'yaml' } as Record<string, string>)[extension] ?? 'text'
}
