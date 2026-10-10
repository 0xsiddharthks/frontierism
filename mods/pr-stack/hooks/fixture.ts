// `gh pr list --json` output for the tests: a stack of three (1 <- 2 <- 3) and one PR alone.
const run = (name: string, conclusion: string, status = 'COMPLETED') => ({ __typename: 'CheckRun', name, status, conclusion })

export const LISTED = [
  { number: 3, title: 'driver', url: 'https://github.com/o/r/pull/3', headRefName: 'c', baseRefName: 'b', isDraft: true, reviewDecision: '', statusCheckRollup: [run('test', 'FAILURE'), run('clippy', 'CANCELLED'), run('fmt', 'SUCCESS')] },
  { number: 1, title: 'tools', url: 'https://github.com/o/r/pull/1', headRefName: 'a', baseRefName: 'main', isDraft: false, reviewDecision: 'APPROVED', statusCheckRollup: [run('test', 'SUCCESS'), run('docs', 'SKIPPED')] },
  { number: 2, title: 'bucket', url: 'https://github.com/o/r/pull/2', headRefName: 'b', baseRefName: 'a', isDraft: false, reviewDecision: 'REVIEW_REQUIRED', statusCheckRollup: [run('test', '', 'IN_PROGRESS'), { __typename: 'StatusContext', context: 'license', state: 'PENDING' }] },
  { number: 4, title: 'alone', url: 'https://github.com/o/r/pull/4', headRefName: 'd', baseRefName: 'main', isDraft: false, reviewDecision: 'CHANGES_REQUESTED', statusCheckRollup: null },
]
