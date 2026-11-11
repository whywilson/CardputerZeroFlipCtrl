#!/usr/bin/env python3
"""Package reviewed project files and exact LVGL sources, never raw dist captures."""
import argparse
import hashlib
import io
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {'.gitignore', 'LICENSE', 'README.md', 'PUBLISH.md', 'build.sh',
              'deploy.sh', 'install.sh', 'run-flipper-one-remote', 'app-builder.json'}
DIRECTORIES = {
    'main': {'.cpp', '.hpp'}, 'config': {'.h'}, 'applications': {'.desktop'},
    'tools': {'.py', '.sh'}, 'tests': {'.py', '.cpp'}, 'docs': {'.md', '.png'},
    'share': {'.md', '.txt', '.png'}, 'design': {'.py', '.png'},
}
EXCLUDED_PARTS = {'.git', '__pycache__', '.DS_Store', 'node_modules', 'build', '.cache'}


def add_bytes(archive, name, data, executable=False):
    info = tarfile.TarInfo('FlipCTL-source/' + name)
    info.size = len(data)
    info.mode = 0o755 if executable else 0o644
    info.mtime = 0
    archive.addfile(info, io.BytesIO(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lvgl', type=Path, required=True,
                        help='Exact LVGL source root containing lvgl.h and src/')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/flipctl-source.tar.gz')
    args = parser.parse_args()
    lvgl = args.lvgl.resolve()
    if not (lvgl / 'lvgl.h').is_file() or not (lvgl / 'src').is_dir():
        parser.error('--lvgl must identify the complete LVGL source directory')
    files = []
    for name in sorted(ROOT_FILES):
        path = ROOT / name
        if path.is_file():
            files.append((name, path))
    for folder, extensions in DIRECTORIES.items():
        for path in sorted((ROOT / folder).rglob('*')):
            relative = path.relative_to(ROOT)
            if any(part in EXCLUDED_PARTS for part in relative.parts):
                continue
            if relative.as_posix() == 'design/key-guide/device-help-preview.png':
                continue
            if path.is_file() and path.suffix in extensions:
                files.append((relative.as_posix(), path))
    for path in sorted(lvgl.rglob('*')):
        relative = path.relative_to(lvgl)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        # Upstream demo/test fixtures are not linked or needed by our build.
        if relative.parts[0] in {'tests', 'demos', 'examples', 'docs', '.github', '.devcontainer'}:
            continue
        if path.is_symlink():
            raise RuntimeError('Review LVGL symlink before packaging: ' + str(relative))
        if path.is_file() and path.suffix not in {'.o', '.a', '.so', '.pyc', '.log'}:
            files.append(('third_party/lvgl/' + relative.as_posix(), path))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    with tarfile.open(args.output, 'w:gz') as archive:
        for name, path in files:
            if path.is_symlink():
                raise RuntimeError('Review project symlink before packaging: ' + name)
            data = path.read_bytes()
            add_bytes(archive, name, data, bool(path.stat().st_mode & 0o111))
            manifest.append(hashlib.sha256(data).hexdigest() + '  ' + name)
        add_bytes(archive, 'SOURCE-SHA256SUMS', ('\n'.join(manifest) + '\n').encode())
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    checksum = args.output.with_suffix(args.output.suffix + '.sha256')
    checksum.write_text(digest + '  ' + args.output.name + '\n')
    print(f'Packaged {len(files)} reviewed source files; {args.output.stat().st_size} bytes')
    print(args.output)


if __name__ == '__main__':
    main()
