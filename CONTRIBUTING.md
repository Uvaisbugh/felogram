# Contributing

Start with the README and product plan. Discuss large features in an issue; small fixes may go directly to a pull request. Keep UI, application logic, and TDLib transport separate. Add meaningful behavior tests using fake transports. Never include real credentials or session files in fixtures.

Run `uv sync --locked --group dev`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, and `uv run pytest` before submitting. Explain the problem, resulting behavior, and verification; disclose manual account checks separately.

Contributions use the MIT license. Be respectful, provide actionable feedback, and protect privacy.
