export type Review = 'approved' | 'changes requested' | 'review required' | 'no review'

export type Pr = {
  number: number
  title: string
  url: string
  head: string
  isDraft: boolean
  review: Review
  passing: number
  pending: number
  // Names of the failing checks.
  failing: string[]
  // How many open PRs this one is stacked on.
  depth: number
}

export type Board = {
  prs: Pr[]
  branch: string
  fetchedAt: number
  error?: string
}

declare module 'claude-code' {
  interface PluginState {
    'pr-stack': { board: Board | null }
  }
}
