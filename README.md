# Version Control Simulator

A Python REPL that models a small in-memory version-control system. It supports repository initialization, commits, branches, graph traversal, commit search, custom sorting, and optional diff/merge behavior.

The project treats commit history as structured data. That makes it useful for practicing graph reasoning, deterministic ordering, searchable metadata, and clear command behavior without relying on external packages.

## Features

- Initialize an in-memory repository
- Create commits and branches
- Switch branches
- Print logs in parent-before-child order
- Sort logs by date or author using custom sorting functions
- Search by keyword or author through inverted indexes
- Find paths and ancestors in the commit graph
- Render simple file diffs
- Create merge commits
- Benchmark insertion sort and merge sort

## Requirements

- Python 3.10 or newer
- No external packages

## Run

```bash
python3 main.py
```

Prompt:

```text
mini-git>
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

## Example

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
mini-git> path c000002 c000003
Path: c000002 -> c000001 -> c000003
mini-git> search login
Found 1 commit:
- c000002: Add login feature (Alice, 2026-05-16 09:30:00)
```

## Project Structure

```text
main.py
minigit/
  cli.py          command parsing and REPL loop
  repository.py   repository state, branches, graph traversal, search
  models.py       commit model
  sorting.py      insertion sort and merge sort helpers
  text_index.py   token normalization
  diff_utils.py   simple line diff renderer
```

## Design Notes

- Commits are stored in a hash map keyed by deterministic session-local IDs.
- Branches map names to commit hashes; the active branch behaves as HEAD.
- The commit graph is a DAG because each new commit points only to existing parents.
- Search uses inverted indexes for keyword and author lookups.
- `PATH` treats commit-parent links as an undirected graph and uses breadth-first search.
- Sorting behavior is implemented directly instead of delegating to Python's built-in sort.
