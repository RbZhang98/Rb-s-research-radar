## Problem and behavior
Research Radar 1.0 mixes a large metadata archive into the reading dashboard and has no place to keep private research notes. This upgrade separates basic/clinical Radars, migrates the exact original 16 A-level recommendations, and keeps DOI deduplication outside the public reading payload.

- Preserve the existing Pages URL and serialized daily workflow. Keep the 1.0 snapshot compressed and verifiable; exclude cleared legacy records from normal backfills.
- Add four clinical journals with source-provided authors/affiliations and independent type/ranking rules. Start clinical accumulation on the first main-branch production update.
- Add singleton DOI favorites in IndexedDB, per-Radar relevance/inspiration profiles, private notes, methods, hypotheses/questions, validated backup/restore and CSV/RIS exports.
- Add local rule-based weekly reports and reviewed keyword suggestions. Personal order never changes public grades or collection scope.
- Publish bounded metadata shards; keep indexes, snapshots and private data out of Pages.

## Validation
Python, JS rule/storage tests and DOM integration pass. Real API smoke tests passed for 14 basic and 4 clinical journals in an isolated activated copy; original 16 survived. Historical clinical validation returned 45 source records (38 with authors and author-linked affiliations), not imported into the production clinical history.

Existing production Pages returned HTTP 200. This branch has not been published; remote Actions execution and real-browser visual/device QA remain for merge/deployment verification. DOM tests use jsdom and fake-indexeddb, not a real browser engine.

## Release / rollback
Keep the stable 1.0 tag before merging. Merge only after user review. The first main workflow sets the accumulation date; launchDate remains null in this PR. Revert the merge PR to roll back code/public data; no migration touches browser IndexedDB.
