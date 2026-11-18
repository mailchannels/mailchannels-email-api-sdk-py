""" Decide whether to publish the latest upstream release tag, without executing upstream code."""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import NoReturn

PROJECT = 'mailchannels'
INDEXES = {'PyPI': 'https://pypi.org', 'TestPyPI': 'https://test.pypi.org'}
RELEASE_TAG = re.compile(r'v\d+\.\d+\.\d+')


def git(*args: str) -> str:
    """Run Git and return its output, failing on a nonzero exit."""
    return subprocess.check_output(['git', *args], text=True).strip()


def fail(message: str) -> NoReturn:
    """Stop the workflow step with a GitHub error annotation."""
    raise SystemExit(f'::error::{message}')


def release_files(version: str) -> list[str]:
    """Return the sorted filenames of a complete release: one pure-Python wheel and the sdist."""
    return sorted([f'{PROJECT}-{version}-py3-none-any.whl', f'{PROJECT}-{version}.tar.gz'])


def latest_tag() -> str:
    """Return the highest vX.Y.Z tag in the mirror."""
    tags = git('tag', '--list', 'v*', '--sort=-version:refname').splitlines()
    for tag in tags:
        if RELEASE_TAG.fullmatch(tag):
            return tag
    fail('No vX.Y.Z release tag found')


def require_on_upstream_main(tag: str, upstream: str) -> None:
    """Fail if the tagged commit is not on canonical Bitbucket main branch (Merge Policies)."""
    git('fetch', '--no-tags', upstream, 'main')
    ancestor = subprocess.run(
        ['git', 'merge-base', '--is-ancestor', f'refs/tags/{tag}^{{commit}}', 'FETCH_HEAD'],
        check=False,
    )
    if ancestor.returncode != 0:
        fail(f'{tag} is not on Bitbucket main. Delete the tag on Bitbucket, then on this '
             'mirror, and tag a commit on main instead.')
    print(f'{tag} is on Bitbucket main')


def require_matching_version(tag: str, version: str) -> None:
    """Fail if __version__ at the tagged commit does not match the tag's version."""
    source = git('show', f'refs/tags/{tag}:src/{PROJECT}/version.py')
    match = re.search(r'^__version__ = "(.*)"$', source, re.MULTILINE)
    found = match.group(1) if match else None
    if found != version:
        fail(f'Tag {tag} does not match __version__ {found!r}')


def index_files(index: str, version: str) -> list[str]:
    """Return the sorted filenames the index lists for the version; empty if it has none."""
    url = f'{INDEXES[index]}/pypi/{PROJECT}/{version}/json'
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return sorted(item['filename'] for item in json.load(response)['urls'])
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return []
        fail(f'{index} returned HTTP {error.code} for {url}')


def should_publish(version: str) -> bool:
    """Return whether to start a release attempt; fail if an earlier attempt left files behind."""
    pypi = index_files('PyPI', version)
    if pypi == release_files(version):
        print(f'{PROJECT} {version} is already on PyPI; nothing to do')
        return False
    
    testpypi = index_files('TestPyPI', version)
    if not pypi and not testpypi:
        print(f'{PROJECT} {version} needs publishing')
        return True
    fail(f'An earlier run already uploaded {PROJECT} {version} '
        f'(PyPI: {pypi or "none"}; TestPyPI: {testpypi}).'
        'To resume, open that earlier run for this tag and use "Re-run failed jobs". '
        'If a code fix is needed, tag a new patch version in Bitbucket instead.')


def write_outputs(**outputs: str) -> None:
    """Expose values to later workflow steps and jobs."""
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as file:
        for name, value in outputs.items():
            file.write(f'{name}={value}\n')


def plan(upstream: str) -> None:
    """Select the latest release tag and decide whether this run should publish it."""
    tag = latest_tag()
    version = tag.removeprefix('v')
    print(f'Latest release tag: {tag}')
    require_on_upstream_main(tag, upstream)
    publish = should_publish(version)
    if publish:
        require_matching_version(tag, version)
    write_outputs(tag=tag, version=version, publish=str(publish).lower())

def main() -> None:
    """Run the requested release step."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest='command', required=True)
    plan_parser = commands.add_parser('plan', help='select the tag and decide whether to publish')
    plan_parser.add_argument('upstream', help='canonical Bitbucket repository URL')
    args = parser.parse_args(sys.argv[1:])
    if args.command == 'plan':
        plan(args.upstream)
    else:
        fail(f'unknown command {args.command}')


if __name__ == '__main__':
    main()
