# PR target adapter

Resolve the repository and PR number first. Record the initial head OID. Collect
the current state without checking out or mutating the branch:

```bash
gh pr view <number> --repo <owner/name> \
  --json number,url,title,state,isDraft,headRefName,headRefOid,baseRefName,baseRefOid,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,files,body,closingIssuesReferences,reviews,comments
gh pr diff <number> --repo <owner/name>
gh pr checks <number> --repo <owner/name>
```

Collect every review thread with GraphQL pagination:

```bash
gh api graphql --paginate \
  -f owner='<owner>' -f name='<name>' -F number=<number> \
  -f query='query($owner:String!,$name:String!,$number:Int!,$endCursor:String){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:100,after:$endCursor){nodes{isResolved isOutdated path line comments(first:100){nodes{author{login}body url createdAt}}}pageInfo{hasNextPage endCursor}}}}}'
```

Read linked issues, accepted specifications, repository rules, changed files,
and the code around risky paths. CI proves only what its named checks exercise.
An unresolved thread blocks merge only when its current, non-outdated claim is
actionable and verified; do not treat thread state alone as correctness proof.
