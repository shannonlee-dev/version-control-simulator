# Mini Git

Mini Git is a Python REPL that models a small in-memory Git-like repository. It supports repository initialization, branches, commits, parent-first logs, direct sorting algorithms, path and ancestor traversal, inverted-index search, plus the optional diff, merge, and sort benchmark features.

## Requirements

- Python 3.10 or newer
- No external package installation

Run it from this directory:

```sh
python3 main.py
```

The prompt is:

```text
mini-git>
```

Use `exit` or `quit` to stop the program.

## Project Structure

```text
main.py        executable entry point
minigit/
  __init__.py    public package exports
  cli.py         command parsing, dispatch, and REPL loop
  repository.py  repository state, branches, commits, search, graph traversal
  models.py      commit data model
  sorting.py     manual insertion sort and merge sort helpers
  text_index.py  search token normalization helpers
  diff_utils.py  optional line diff renderer
```

## Commands

```text
INIT <user_name>
BRANCH <branch_name>
SWITCH <branch_name>
COMMIT <message>
LOG
LOG --sort-by=date
LOG --sort-by=author
PATH <commit1> <commit2>
ANCESTORS <commit_hash>
SEARCH <keyword>
SEARCH --author=<name>
diff <file1> <file2>
merge <branch_name>
bench-sort [size]
exit
quit
```

Commands are case-insensitive. String arguments with spaces can be wrapped in quotes:

```text
init "Alice Doe"
commit "Add login feature"
search "login"
search --author="Alice Doe"
```

Invalid input uses short standardized messages such as:

```text
Invalid args
Unknown branch: <name>
Unknown commit: <hash>
Unknown file: <path>
```

## Example Session

```text
mini-git> init "Alice"
Initialized repository.
Current branch: main
Current user: Alice
mini-git> commit "Initial commit"
[main c000001] Initial commit
mini-git> branch feature
Created branch: feature
mini-git> switch feature
Switched to branch: feature
mini-git> commit "Add login feature"
[feature c000002] Add login feature
mini-git> switch main
Switched to branch: main
mini-git> commit "Add payment feature"
[main c000003] Add payment feature
mini-git> log
commit c000001 (Alice, 2026-05-16 09:30:00)
parents: -
Initial commit
commit c000002 (Alice, 2026-05-16 09:30:00) [feature]
parents: c000001
Add login feature
commit c000003 (Alice, 2026-05-16 09:30:00) [main]
parents: c000001
Add payment feature
mini-git> path c000002 c000003
Path: c000002 -> c000001 -> c000003
mini-git> search login
Found 1 commit:
- c000002: Add login feature (Alice, 2026-05-16 09:30:00)
mini-git> quit
Bye.
```

Timestamps come from the current runtime clock, so they will differ between runs.

## Implementation Notes

- Commits are stored in a hash map keyed by commit hash for fast lookup.
- Commit hashes are deterministic session-local IDs: `c000001`, `c000002`, and so on.
- Each commit stores `hash`, `message`, `author`, `timestamp`, and `parents`.
- Branches map branch names to commit hashes. The current branch is the active HEAD.
- The commit graph is a DAG because new commits only point to existing parent commits.
- Keyword search and author search use inverted indexes:
  - `keyword -> commit hashes`
  - `author -> commit hashes`
- Message keywords are split on whitespace and normalized to lowercase.
- `LOG` prints commits in creation order, which is parent-before-child because a child is only created after its parents exist.
- `PATH` treats commit-parent links as undirected edges and uses breadth-first levels. If several shortest paths exist, it chooses the lexicographically smallest `hash->hash` path string.
- `ANCESTORS` walks parent links and prints every reachable ancestor.
- File contents are not tracked as repository data. The program keeps commit metadata in memory and does not write repository state to disk.
- There is no network access or external service dependency.

## Direct Sorting Algorithms

The program does not call Python standard sorting APIs for Mini Git behavior. It implements:

- `insertion_sort`: stable, simple, average and worst-case `O(n^2)`
- `merge_sort_custom`: stable, average and worst-case `O(n log n)`

`LOG --sort-by=date` and `LOG --sort-by=author` use the manual insertion sort with different comparison keys.

The optional `bench-sort [size]` command compares the two algorithms on reverse-ordered integer input. Example:

```text
mini-git> bench-sort 100
Sort benchmark size=100
insertion_sort_seconds=0.000300
merge_sort_seconds=0.000180
```

The exact timings depend on the computer and current load. In general, insertion sort is easy to understand but grows quadratically, while merge sort scales better for larger inputs.

## Bonus Features

`diff <file1> <file2>` reads two existing text files and prints common, deleted, and added lines:

```text
Diff:
  same line
- old line
+ new line
```

`merge <branch_name>` creates a merge commit on the current branch with two parents: the current branch HEAD and the target branch HEAD.
