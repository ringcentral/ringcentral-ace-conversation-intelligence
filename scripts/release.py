"""Prepare and publish a validated release; invoked only by the manual release workflow."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from plugin_repo import check, set_version

VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')


def run(root, *args):
    return subprocess.check_output(args, cwd=root, text=True).strip()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def changes(root):
    paths = run(root, 'git', 'diff', '--name-only', 'HEAD', '-z').split('\0')
    untracked = run(root, 'git', 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
    return {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths+untracked if p}


def prepare(root, version, state_file):
    version = version.removeprefix('v')
    require(VERSION.fullmatch(version), 'Use a version such as v1.1.0 or 1.1.0, without prerelease suffixes')
    require(not run(root, 'git', 'status', '--porcelain'), 'Release preparation needs a clean checkout')
    require(run(root, 'git', 'branch', '--show-current') == 'main', 'Start release preparation on main')
    tag = 'v'+version
    base = run(root, 'git', 'rev-parse', 'HEAD')
    tags = run(root, 'git', 'tag', '--list').splitlines()
    resume = tag in tags
    if resume:
        commit = run(root, 'git', 'rev-parse', tag+'^{commit}')
        require(subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=root).returncode == 0,
                'Existing release tag is not on main')
        # Read and validate before changing the checkout; never move an existing tag.
        tagged = json.loads(run(root, 'git', 'show', tag+':plugins/openai/plugin.json'))
        require(tagged['version'] == version, 'Existing tag does not match its manifest version')
        run(root, 'git', 'checkout', '--detach', commit)
        changelog = (root/'CHANGELOG.md').read_text()
        match = re.search(r'^## '+re.escape(version)+r' — [^\n]+\n(.*?)(?=^## |\Z)', changelog, re.M | re.S)
        require(match, 'Existing tag has no versioned changelog entry')
        notes = match.group(1).strip()
    else:
        manifest_path = root/'plugins/openai/plugin.json'
        manifest = json.loads(manifest_path.read_text())
        current = manifest['version']
        require(tuple(map(int, version.split('.'))) > tuple(map(int, current.split('.'))),
                'New release version must be greater than the current manifest version')
        release_tags = [t for t in tags if t.startswith('v') and VERSION.fullmatch(t[1:])]
        require(all(tuple(map(int, version.split('.'))) > tuple(map(int, t[1:].split('.'))) for t in release_tags),
                'New release version must be greater than existing version tags')
        check(root)
        changelog = (root/'CHANGELOG.md').read_text()
        require(changelog.count('## Unreleased\n') == 1, 'Expected one Unreleased changelog section')
        require(not re.search(r'^## '+re.escape(version)+r'(?:\s|$)', changelog, re.M), 'Version already exists in changelog')
        before, rest = changelog.split('## Unreleased\n', 1)
        upcoming, separator, history = rest.partition('\n## ')
        notes = upcoming.strip()
        require(notes, 'Add release notes under ## Unreleased in CHANGELOG.md before releasing')
        set_version(root, version)
        (root/'CHANGELOG.md').write_text(before+'## Unreleased\n\n## '+version+' — '+date.today().isoformat()+'\n\n'+notes+'\n'+separator+history)
    check(root, tag=tag)
    state = {'version': version, 'tag': tag, 'base': base, 'resume': resume,
             'head': run(root, 'git', 'rev-parse', 'HEAD'), 'changes': changes(root), 'notes': notes}
    state_file.write_text(json.dumps(state, indent=2)+'\n')


def publish_assets(root, tag, notes):
    """Resume drafts; verify published assets byte-for-byte without replacing them."""
    lookup = subprocess.run(['gh', 'api', 'repos/{owner}/{repo}/releases/tags/'+tag],
                            cwd=root, capture_output=True, text=True)
    if lookup.returncode:
        require('(HTTP 404)' in lookup.stderr, 'Could not inspect GitHub release: '+lookup.stderr)
        release = None
    else:
        release = json.loads(lookup.stdout)
    with tempfile.TemporaryDirectory(prefix='rc-release-') as directory:
        temp = Path(directory)
        body = temp/'notes.md'
        body.write_text(notes+'\n')
        assets = sorted((root/'dist').iterdir())
        plugin_name = json.loads((root/'plugins/openai/plugin.json').read_text())['name']
        require(len(assets) == 3 and {p.name for p in assets} == {'SHA256SUMS', f'{plugin_name}-claude-{tag[1:]}.zip', f'{plugin_name}-openai-{tag[1:]}.zip'},
                'Expected exactly two versioned ZIPs and SHA256SUMS')
        if release and not release['draft']:
            require(not release['prerelease'], 'Refusing to promote a prerelease')
        else:
            if release is None:
                run(root, 'gh', 'release', 'create', tag, '--verify-tag', '--draft', '--title', tag, '--notes-file', str(body))
            else:
                require({a['name'] for a in release.get('assets', [])} <= {p.name for p in assets},
                        'Draft has unexpected assets; review them before retrying')
            run(root, 'gh', 'release', 'upload', tag, *(str(p) for p in assets), '--clobber')
            run(root, 'gh', 'release', 'edit', tag, '--draft=false', '--prerelease=false', '--title', tag, '--notes-file', str(body))
        # Every path verifies the public artifacts before the release is considered complete.
        downloaded = temp/'download'; downloaded.mkdir()
        run(root, 'gh', 'release', 'download', tag, '--dir', str(downloaded))
        require({p.name: p.read_bytes() for p in downloaded.iterdir()} == {p.name: p.read_bytes() for p in assets},
                'Published release assets differ; refusing to replace them or complete the release')


def publish(root, state_file):
    state = json.loads(state_file.read_text())
    tag = state['tag']
    require(run(root, 'git', 'rev-parse', 'HEAD') == state['head'] and changes(root) == state['changes'],
            'Checkout changed after release preparation')
    check(root, tag=tag)
    if not state['resume']:
        require(state['changes'], 'No prepared version changes')
        run(root, 'git', 'add', '--', *sorted(state['changes']))
        run(root, 'git', 'commit', '-m', 'Release '+tag)
        run(root, 'git', 'tag', '-a', tag, '-m', 'Release '+tag)
        # A concurrent main update rejects both refs; no force or tag replacement.
        run(root, 'git', 'push', '--atomic', 'origin', 'HEAD:refs/heads/main', 'refs/tags/'+tag)
    commit = run(root, 'git', 'rev-parse', 'HEAD')
    remote_tag = run(root, 'git', 'ls-remote', 'origin', 'refs/tags/'+tag, 'refs/tags/'+tag+'^{}')
    require(any(line == commit+'\trefs/tags/'+tag+suffix for line in remote_tag.splitlines() for suffix in ('', '^{}')),
            'Remote release tag does not match validated commit')
    publish_assets(root, tag, state['notes'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'publish'))
    parser.add_argument('--version')
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='Checkout to release when the control scripts run from a separate directory')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command == 'prepare':
            require(args.version is not None, '--version is required')
            prepare(root, args.version, args.state)
        else:
            publish(root, args.state)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'ERROR: {error}\n')


if __name__ == '__main__':
    main()
