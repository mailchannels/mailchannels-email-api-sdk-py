# Development

This project uses uv for Python package management. Run the full local checks
before committing changes:

```bash
uv sync --extra async --extra dev
uv run pytest
uv run pytest --cov --cov-report=term-missing
uv run ruff check src tests examples scripts typing_tests
uv run mypy
uv run python scripts/run_consumer_typing.py
uv build
uv run python scripts/smoke_wheel_install.py
uv run python scripts/check_openapi_drift.py
uv run python scripts/generate_api_coverage.py
uv run python scripts/generate_api_reference.py
uv run python scripts/regen_readme_version.py
```

Current uv releases do not expose `uv pytest` as a native subcommand; use
`uv run pytest` for the portable pytest harness.

## CI

Bitbucket Pipelines is configured in
[bitbucket-pipelines.yml](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/bitbucket-pipelines.yml).
On every push it runs ruff, mypy, pytest with coverage (85% branch threshold),
the OpenAPI drift check, the external consumer type check, and a clean wheel
install smoke test. The 3.9–3.13 Python matrix runs on every merge to `main`
and can also be triggered ad-hoc as the `multi-python` custom pipeline. A
separate `online-tests` custom pipeline runs the live API tests on demand and
expects `MAILCHANNELS_API_KEY` (and optionally `MAILCHANNELS_API_URL`,
`MAILCHANNELS_ONLINE_FROM`, `MAILCHANNELS_ONLINE_TO`) configured as repository
or deployment variables in Bitbucket.

The unit test suite includes direct transport-wrapper tests, explicit API
error mapping tests, strict response model validation, negative email payload
tests, README snippet smoke tests, external-consumer type checks, and clean
wheel install checks with and without the `[async]` extra. It also verifies
that the README API-version line
([tests/test_readme_version.py](https://bitbucket.org/mailchannels/mailchannels-email-api-sdk-py/src/main/tests/test_readme_version.py))
stays in sync with `API_SPEC_COMPATIBILITY`.

## Publishing to PyPI

Publishing is driven by Bitbucket Pipelines. PyPI does not have a native
Bitbucket integration for trusted publishing, so the pipeline authenticates
with an API token.

- **TestPyPI publish** (<https://test.pypi.org/>) runs automatically on every
  merge to `main`, after the full check suite and the 3.9–3.13 Python
  matrix all pass. It uses `twine upload --skip-existing`, so a merge that
  doesn't change `__version__` in `src/mailchannels/version.py` succeeds silently without
  republishing the same artifact. The `custom: publish-testpypi` trigger
  also uploads real artifacts to TestPyPI; it is not an upload-free dry run.
- **Real PyPI publish** (<https://pypi.org/>) runs only when you manually
  trigger the `custom: publish-pypi` pipeline from the Bitbucket UI. We'll
  move this onto a tag trigger (`pipelines.tags: 'v*'`) once the release
  cadence settles down.

Both pipelines run the full check suite (`*checks`) first; the publish step
only fires if checks pass.

### One-time setup

1. Create a PyPI account at <https://pypi.org/> and a TestPyPI account at
   <https://test.pypi.org/>. The two are separate accounts with separate
   tokens.
2. Generate an API token scoped to the `mailchannels` project on each. The
   tokens look like `pypi-AgEIc...`.
3. In Bitbucket, open **Repository settings → Repository variables** and add
   two **secured** variables:
   - `PYPI_API_TOKEN` — the real PyPI token.
   - `PYPI_TEST_API_TOKEN` — the TestPyPI token.

   Marking them secured prevents them from appearing in pipeline logs.

### Release procedure

1. Update `__version__` in `src/mailchannels/version.py`, commit the bump, and
   merge the commit into `main` through your normal workflow. `pyproject.toml`
   declares a dynamic version read from this file via Hatch; do not add a static
   project version. Select an unused version and verify the built metadata.
2. Wait for the `branches.main` pipeline to complete. The matrix runs,
   then the TestPyPI publish step automatically uploads the new artifact
   (it skips silently if the version hasn't changed).
3. Download the exact release wheel from TestPyPI, then install that local file
   with dependencies from PyPI in a clean venv. Run these commands from the
   reviewed release checkout. Do not combine indexes with `--extra-index-url`: pip
   does not prioritize TestPyPI and could select the package from production PyPI.
   Use a clean pip configuration without extra indexes/find-links; the first
   command must retrieve the SDK wheel only from TestPyPI:

   ```bash
   release_version=$(python -c 'import runpy; print(runpy.run_path("src/mailchannels/version.py")["__version__"])')
   testpypi_check=$(mktemp -d)
   python -m venv "$testpypi_check/venv"
   source "$testpypi_check/venv/bin/activate"
   python -m pip download --no-deps --only-binary=:all: \
       --index-url https://test.pypi.org/simple/ \
       --dest "$testpypi_check/wheels" "mailchannels==$release_version"
   python -m pip hash "$testpypi_check"/wheels/mailchannels-*.whl
   # Compare with the SHA256 on this exact TestPyPI release's file page.
   # This checks downloaded bytes against the index; it is not independent provenance.
   python -m pip install --index-url https://pypi.org/simple/ \
       "$testpypi_check"/wheels/mailchannels-*.whl
   python -c 'import importlib.metadata, sys; assert importlib.metadata.version("mailchannels") == sys.argv[1]' "$release_version"
   deactivate
   ```

4. If the TestPyPI validation looks right, trigger **Pipelines → Run pipeline → Custom →
   `publish-pypi`** on the release commit from the Bitbucket UI to push to
   real PyPI.
5. Tag the release commit and push the tag:

   ```bash
   release_version=$(python -c 'import runpy; print(runpy.run_path("src/mailchannels/version.py")["__version__"])')
   git tag -s "v${release_version}" -m "Release v${release_version}"
   git push origin "refs/tags/v${release_version}"
   ```

A given version on PyPI is immutable — if you upload a broken artifact, you
must bump the patch version and republish. The TestPyPI step exists exactly
to catch that before it can happen on real PyPI.

### Publishing from a local machine (fallback)

If you ever need to publish without Bitbucket (e.g., the pipeline is down),
the same flow works locally. Store both tokens in `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-...your-pypi-token...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-...your-testpypi-token...
```

`chmod 600 ~/.pypirc` so the tokens are not world-readable. Then run:

```bash
rm -rf dist/
uv build
uvx --with twine==7.0.0 twine check dist/*
uvx --with twine==7.0.0 twine upload --repository testpypi dist/*  # real TestPyPI upload
uvx --with twine==7.0.0 twine upload dist/*                        # real publish
```

## Online API Tests

The default test suite never calls the live MailChannels API. Online tests are
marked with `online` and run only when you both provide a real API key in the
environment and pass `--online`.

```bash
export MAILCHANNELS_API_KEY="your_real_mailchannels_api_key"
uv run pytest -m online --online
```

The online suite includes parent-account usage, async usage, volume metrics,
sub-account listing, suppression listing, webhook listing, optional domain
checks, DKIM listing, dry-run sending, and dry-run rejection checks for
malformed raw send payloads. The volume metrics test sends an explicit 24-hour
`start_time` and `end_time` window so the live service does not need to infer an
unbounded range. The send tests use MailChannels dry runs, which do not deliver
messages. Set sender and recipient addresses to enable those dry-run tests:

```bash
export MAILCHANNELS_ONLINE_FROM="sender@example.com"
export MAILCHANNELS_ONLINE_TO="recipient@example.net"
uv run pytest -m online --online
```

To run the optional `/check-domain` and DKIM listing tests, provide a domain
that belongs to the account:

```bash
export MAILCHANNELS_ONLINE_DOMAIN="example.com"
uv run pytest -m online --online
```

The suite also includes a test that sends a real email through `/send`. It is
disabled unless you explicitly opt in with `MAILCHANNELS_ONLINE_SEND_REAL=1`:

```bash
export MAILCHANNELS_ONLINE_FROM="sender@example.com"
export MAILCHANNELS_ONLINE_TO="recipient@example.net"
export MAILCHANNELS_ONLINE_SEND_REAL=1
uv run pytest tests/test_online_api.py::test_online_send_real_email --online
```

Use `MAILCHANNELS_API_URL` if you need to point the online tests at a non-default
MailChannels API host.

If the live MailChannels service returns a 5xx response, times out, or drops a
connection for an online endpoint, that test is reported as `xfail` because the
failure is outside the local SDK behavior being tested. Authentication and
authorization errors still fail the test normally.

Destructive online CRUD tests are marked `online_destructive` and stay disabled
unless you pass both `--online` and `--online-destructive` and set
`MAILCHANNELS_ONLINE_DESTRUCTIVE=1`. Run these only against a dedicated test
account because they create and delete suppressions, sub-accounts, credentials,
limits, and webhook configuration. The MailChannels webhook delete endpoint
removes all configured webhooks.

```bash
export MAILCHANNELS_ONLINE_DESTRUCTIVE=1
uv run pytest -m online_destructive --online --online-destructive
```

## Containerized Verification

Run the full suite in Docker on Linux or SmolVM on macOS before committing.

### Linux: Docker

From the repository root, create a source archive and mount it read-only into
a disposable Python container. The environment and build artifacts remain
inside the container, avoiding root-owned files in your checkout:

```bash
tar --exclude .venv --exclude .git --exclude dist --exclude .mypy_cache --exclude .ruff_cache --exclude .pytest_cache --exclude .env --exclude '.env.*' -cf /tmp/mailchannels-python-sdk.tar .
docker run --rm --mount type=bind,src=/tmp/mailchannels-python-sdk.tar,dst=/tmp/sdk.tar,readonly python:3.13-slim sh -ec '
  mkdir -p /workspace
  tar -xf /tmp/sdk.tar -C /workspace
  cd /workspace
  pip install uv
  uv sync --extra async --extra dev
  uv run pytest --cov --cov-report=term-missing
  uv run python scripts/check_skill_snippets.py
  uv run ruff check src tests examples scripts typing_tests
  uv run mypy
  uv run python scripts/run_consumer_typing.py
  uv build
  uv run python scripts/smoke_wheel_install.py
  uv run python scripts/check_openapi_drift.py
'
```

This runs the offline suite without forwarding API credentials. Live API tests
remain a separate, explicitly configured workflow.

### macOS: SmolVM

In the macOS sandbox, copying a tar
archive into the VM is more reliable than a direct bind mount:

```bash
COPYFILE_DISABLE=1 tar --exclude .venv --exclude .git --exclude dist --exclude .mypy_cache --exclude .ruff_cache --exclude .pytest_cache --exclude .env --exclude '.env.*' -cf /tmp/mailchannels-python-sdk.tar .
smolvm machine create mc-sdk-tests --net --image python:3.13-slim
smolvm machine start --name mc-sdk-tests
smolvm machine cp /tmp/mailchannels-python-sdk.tar mc-sdk-tests:/workspace/mailchannels-python-sdk.tar
smolvm machine exec --name mc-sdk-tests -- sh -lc 'cd /workspace && mkdir -p mailchannels-python-sdk && tar -xf mailchannels-python-sdk.tar -C mailchannels-python-sdk && cd mailchannels-python-sdk && pip install uv && uv sync --extra async --extra dev && uv run pytest'
smolvm machine stop --name mc-sdk-tests
```
