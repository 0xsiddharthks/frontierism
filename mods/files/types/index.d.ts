export type View = 'all' | 'changes' | 'session'
export type Activity = 'read' | 'edited'
export type PreviewMode = 'content' | 'diff'
export type FileSnapshot = {
  root: string
  cwd: string
  paths: string[]
  changes: { path: string; status: string; oldPath?: string }[]
  total: number
  truncated: boolean
}
export type Preview = { kind: PreviewMode; source: string; note: string }
export type FilesState = {
  snapshot: FileSnapshot | null
  view: View
  query: string
  collapsed: string[]
  page: number
  selected: string[]
  active: string | null
  mode: PreviewMode
  preview: Preview | null
  previewPage: number
  activity: Record<string, Activity>
  error?: string
  notice?: string
}

declare module 'claude-code' {
  interface PluginState {
    files: { browser: FilesState }
  }
}
