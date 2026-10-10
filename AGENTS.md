## Dev environment tips
- Use uv for Python package management and manage this project as a uv project.
- The `rg` command is installed; use it for quick searching.
- Development hosts may run Linux or macOS. Use Docker on Linux and SmolVM on macOS for containerized verification; see `docs/DEVELOPMENT.md`.
- The canonical Git server is Bitbucket; inspect the configured remote before publishing changes.
- This repository has multiple developers. Work on a feature branch and submit a Bitbucket pull request for review; do not push changes directly to main.
- Update README.md with each major commit.
- Don't use README.md as a change log. It's user documentation; they don't go there to look for changes.
- Update the agent-facing skill under `.agents/skills/mailchannels-python/` with each change to this repo so future LLMs know how to use the MailChannels Python SDK correctly. `SKILL.md` is the entry point with the decision tree; per-topic recipes live in `resources/`.
- After updating any file under `.agents/skills/mailchannels-python/`, run `uv run python scripts/check_skill_snippets.py` to confirm every Python snippet still type-checks against the current SDK source. The script auto-injects standard dummy names (`message`, `payload`, `result`, `logger`, `some_coroutine`); when a fragment intentionally won't type-check (bare `except`, partial method body, etc.) mark its first non-blank line with `# type-check: skip`.

## Dev rules
- Use Python logging liberally to insert judicious debug, info, warning, and error messages in the code.
- Import logging into each module and set logger = logging.getLogger(__name__). Then use logger for logging in that module.
- In most cases where an error message is called for, you should raise an appropriate exception after logging the error.
- Let exceptions bubble up to the caller unless there is a logical way to handle the exception within the current scope.
- Unless there is no more specific alternative, never catch the base `Exception` class. Always catch the most specific exception you can.
- Commit every change you make and ask the user to push changes when a significant batch of changes has been made.
- Use Python type hints, data classes, Pydantic models, and other strong typing features everywhere.
- Never write a function that has no typing on parameters.
- Write a documentation string for every function and every class.
- Keep functions short and modular. If a function grows longer than 50 rows or so, break it into separate functions that you can compose in a sequence.
- Take the time to keep your code clean, tidy, and readable. Comments should not be required if code is written in a modular, readable manner.
- Always run tests in a containerized environment: Docker on Linux, or https://github.com/smol-machines/smolvm on macOS. Follow the platform-specific commands in `docs/DEVELOPMENT.md`.

## Testing instructions
- Add or update tests for the code you change, even if nobody asked.
- Use pytest and create a harness so the user can just type "uv pytest".
- Always run the full test suite before every commit. Never commit if the test suite fails to pass.
