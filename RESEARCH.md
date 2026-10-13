# Research — git-ref-retention

Observed 13 October 2026 on live GitHub. Demand is inferred from documented workflows and public issues, not a verified request for this product. Only the first page of each star-sorted problem search was reviewed; this is not an exhaustive global ranking. Broad unrelated results were excluded. Stars are discovery signals, not technical performance evidence.

## User and acceptance

A maintainer investigating why a large Git blob remains reachable after a proposed ref cleanup.

Pain: Show which remaining Git refs retain large blobs before a proposed ref drop.

Smallest useful capability and acceptance: Dropping an archive branch alone retains its blob via a tag; dropping both loses named roots; checking out that commit retains it through HEAD; exact size thresholds work; annotated tags retain; shallow/promisor/unknown roots fail; refs and worktree remain unchanged.

## Observed alternatives

| Repository | Stars | Last push (UTC) | Status / detected license |
| --- | ---: | --- | --- |
| [github/git-sizer](https://github.com/github/git-sizer) | 4081 | 2026-10-06T02:50:39Z | active repository / MIT |
| [newren/git-filter-repo](https://github.com/newren/git-filter-repo) | 13384 | 2026-07-09T22:09:49Z | active repository / NOASSERTION |
| [rtyley/bfg-repo-cleaner](https://github.com/rtyley/bfg-repo-cleaner) | 12199 | 2025-01-19T18:52:14Z | active repository / GPL-3.0 |

Query: `git size`; [GitHub search, Most stars](https://github.com/search?q=git%20size&type=repositories&s=stars&o=desc). Exact observed queries, stars and push dates are recorded above. Highest-star relevant result on that page: github/git-sizer. Other established workflow alternatives were reviewed even if they were not on that first page.

Git-sizer reports repository size and graph metrics, and its README distinguishes named-ref reachability from reflogs and unreachable objects. Git-filter-repo provides analysis plus history rewrite; BFG cleans large/sensitive blobs. This tool returns exact remaining named-root witnesses for reported large blobs under an explicit proposed ref drop, without any rewrite. It is not a compressed-space estimate or full history-cleaning replacement.

## Differentiation and discovery

Existing PatchGym creates coding-agent tasks from history; this explains object retention, with no task generation or rewriting. Discover through synthetic large-blob/tag retention examples.

## Fair comparison boundary

Docs, relevant source and accessible issue collections were inspected. No comparator was installed or timed on equivalent workloads; therefore no install-speed, reliability or performance superiority is claimed. A passing example proves our documented behavior only. No external code was reused; comparator licenses above are API-detected labels, not a legal determination. Support and licensing follow each upstream repository; this alpha offers MIT source and best-effort issue support.
