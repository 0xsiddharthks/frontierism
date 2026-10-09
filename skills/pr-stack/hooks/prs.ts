import type { Pr, Review } from '../types'

export const FIELDS = 'number,title,url,headRefName,baseRefName,isDraft,reviewDecision,statusCheckRollup'

// One entry of `gh pr list --json statusCheckRollup`: a check run or a commit status.
type Check = {
  name?: string
  context?: string
  status?: string
  conclusion?: string
  state?: string
}

type Listed = {
  number: number
  title: string
  url: string
  headRefName: string
  baseRefName: string
  isDraft: boolean
  reviewDecision?: string
  statusCheckRollup?: Check[] | null
}

const PASSED = new Set(['SUCCESS', 'NEUTRAL', 'SKIPPED'])
const WAITING = new Set(['PENDING', 'EXPECTED'])
const REVIEWS: Record<string, Review> = {
  APPROVED: 'approved',
  CHANGES_REQUESTED: 'changes requested',
  REVIEW_REQUIRED: 'review required',
}

function tally(checks: readonly Check[]): Pick<Pr, 'passing' | 'pending' | 'failing'> {
  const failing: string[] = []
  let passing = 0
  let pending = 0
  for (const check of checks) {
    // A check run carries `status` and `conclusion`; a commit status only `state`.
    const isRun = check.status !== undefined
    const result = isRun ? check.conclusion : check.state
    if (isRun ? check.status !== 'COMPLETED' : WAITING.has(result ?? '')) pending += 1
    else if (PASSED.has(result ?? '')) passing += 1
    else failing.push(check.name ?? check.context ?? 'check')
  }
  return { passing, pending, failing }
}

/** `gh pr list` output as rows, each stack listed base first with its dependents beneath it. */
export function toRows(json: string): Pr[] {
  const listed = JSON.parse(json) as Listed[]
  const heads = new Set(listed.map(pr => pr.headRefName))
  const rows: Pr[] = []
  const seen = new Set<number>()
  const place = (pr: Listed, depth: number) => {
    if (seen.has(pr.number)) return
    seen.add(pr.number)
    rows.push({
      number: pr.number,
      title: pr.title,
      url: pr.url,
      head: pr.headRefName,
      isDraft: pr.isDraft,
      review: REVIEWS[pr.reviewDecision ?? ''] ?? 'no review',
      ...tally(pr.statusCheckRollup ?? []),
      depth,
    })
    for (const child of listed) if (child.baseRefName === pr.headRefName) place(child, depth + 1)
  }
  for (const pr of listed) if (!heads.has(pr.baseRefName)) place(pr, 0)
  // Whatever a cycle of bases left unplaced still shows.
  for (const pr of listed) place(pr, 0)
  return rows
}

export const ciLine = (pr: Pr): string => {
  const parts = [
    ...(pr.failing.length > 0 ? [`✗ ${pr.failing.length}`] : []),
    ...(pr.pending > 0 ? [`● ${pr.pending}`] : []),
    ...(pr.passing > 0 ? [`✓ ${pr.passing}`] : []),
  ]
  return parts.length === 0 ? 'no checks' : parts.join('  ')
}

export const ciColor = (pr: Pr): string | undefined =>
  pr.failing.length > 0 ? 'red' : pr.pending > 0 ? 'yellow' : pr.passing > 0 ? 'green' : undefined
