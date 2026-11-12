"""Verify that TestPyPI holds exactly the distributions built for a release."""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ATTEMPTS = 10
RETRY_SECONDS = 30


def local_hashes(dist: Path) -> dict[str, str]:
    """Return the SHA256 of each built distribution, keyed by filename."""
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in dist.iterdir()
    }


def testpypi_hashes(version: str) -> dict[str, str]:
    """Return the SHA256 of each file TestPyPI lists for the version, by filename."""
    url = f'https://test.pypi.org/pypi/mailchannels/{version}/json'
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            files = json.load(response)['urls']
    except urllib.error.HTTPError as error:
        print(f'TestPyPI returned HTTP {error.code}')
        return {}
    return {item['filename']: item['digests']['sha256'] for item in files}


def main() -> None:
    """Fail unless TestPyPI lists the same filenames and hashes as the local build."""
    version, dist = sys.argv[1], Path(sys.argv[2])
    local = local_hashes(dist)
    # TestPyPI's JSON API can lag behind a fresh upload; retry while files are missing.
    for attempt in range(1, ATTEMPTS + 1):
        remote = testpypi_hashes(version)
        missing = sorted(set(local) - set(remote))
        if not missing:
            break
        print(f'Waiting for TestPyPI to list {missing} (attempt {attempt}/{ATTEMPTS})')
        time.sleep(RETRY_SECONDS)
    else:
        raise SystemExit(f'::error::Mismatched release found on TestPyPI for {version}')
    if remote != local:
        for name in sorted(set(local) | set(remote)):
            print(f'{name}: local={local.get(name)} testpypi={remote.get(name)}')
        raise SystemExit(f'::error::TestPyPI files for {version} differ from this '
                         'build; release a new patch version instead')
    print('TestPyPI files match the build')


if __name__ == '__main__':
    main()
