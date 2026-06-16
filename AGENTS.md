# AGENTS.md

You are an AI coding agent (Copilot, Claude Code, Cursor, Gemini, or similar) working in this repository. Use this file as the index to the project's docs. The docs are the source of truth — read them directly and follow their rules.

## Where to look

| If you are... | Read |
|---|---|
| Getting oriented (what this project is, how to run it) | [`README.md`](README.md) |
| Setting up the dev environment or opening a PR | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Writing or modifying tests | [`docs/testing/TEST_FORMAT.md`](docs/testing/TEST_FORMAT.md) |
| Deciding what cases to cover for a feature | [`docs/testing/TEST_COVERAGE.md`](docs/testing/TEST_COVERAGE.md) |
| Placing a new test in the tree | [`docs/testing/FOLDER_STRUCTURE.md`](docs/testing/FOLDER_STRUCTURE.md) |
| Reviewing a pull request | [`docs/REVIEW.md`](docs/REVIEW.md) |
| Identifying maintainers / points of contact | [`MAINTAINERS.md`](MAINTAINERS.md) |
| Looking up the feature taxonomy (operators, stages, commands) | [`docs/feature-tree.csv`](docs/feature-tree.csv) |

## How to use the docs

1. **Writing or modifying a test** → read [`TEST_FORMAT.md`](docs/testing/TEST_FORMAT.md) and [`FOLDER_STRUCTURE.md`](docs/testing/FOLDER_STRUCTURE.md) before you start. Then check [`TEST_COVERAGE.md`](docs/testing/TEST_COVERAGE.md) for the feature category's required cases.
2. **Reviewing a PR** → read [`docs/REVIEW.md`](docs/REVIEW.md) end-to-end and apply its severity levels, per-section checklist, and "what not to flag" rules.
3. **Running the suite or setting up locally** → use [`README.md`](README.md) for usage and [`CONTRIBUTING.md`](CONTRIBUTING.md) for dev setup, hooks, and DCO.
4. **Before committing** → activate the repo's virtualenv so pre-commit hooks (which invoke `python` on `PATH`) succeed, and sign off every commit with `git commit -s`. DCO is enforced.

When a rule lives in one of the linked docs, follow that doc — it is authoritative.
