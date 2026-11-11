#!/usr/bin/env python3
"""Build and inspect the reviewed arm64 FlipCTL Debian package without root.

Requires dpkg-deb and an AArch64-capable readelf. The current tested executable
must already exist at dist/flipper-one-remote. SOURCE_DATE_EPOCH defaults to 0;
identical inputs and packaging-tool versions produce identical package bytes.
"""
import hashlib
import io
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'flipper-one-remote'
VERSION = '0.1.0'
ARCH = 'arm64'
MAINTAINER = 'Wilson <15230131+whywilson@users.noreply.github.com>'
HOMEPAGE = 'https://github.com/whywilson/CardputerZeroFlipCtrl'
BASE = 'usr/share/APPLaunch'
APP = BASE + '/apps/' + PACKAGE
OUTPUT_NAME = f'{PACKAGE}_{VERSION}_{ARCH}.deb'
NEEDED_PACKAGES = {
    'libfreetype.so.6': 'libfreetype6',
    'libpng16.so.16': 'libpng16-16 | libpng16-16t64',
    'libz.so.1': 'zlib1g',
    'libstdc++.so.6': 'libstdc++6 (>= 5)',
    'libgcc_s.so.1': 'libgcc-s1',
    'libm.so.6': None,  # Provided by libc6.
    'libc.so.6': None,
}


def run(command, **kwargs):
    return subprocess.run(command, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, **kwargs).stdout


def find_tool(names):
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError('Required tool not found: ' + ' or '.join(names))


def version_tuple(value):
    return tuple(int(part) for part in value.split('.'))


def elf_dependencies(binary, readelf, env):
    header = binary.read_bytes()[:20]
    if (len(header) != 20 or header[:6] != b'\x7fELF\x02\x01' or
            struct.unpack_from('<H', header, 18)[0] != 183):
        raise RuntimeError('Expected a little-endian ELF64 AArch64 executable')
    dynamic = run([readelf, '--dynamic', str(binary)], env=env).decode()
    needed = re.findall(r'\(NEEDED\).*\[([^\]]+)\]', dynamic)
    unknown = sorted(set(needed) - set(NEEDED_PACKAGES))
    if unknown or not needed:
        raise RuntimeError('Review unrecognized ELF dependencies: ' + repr(unknown or needed))
    versions = run([readelf, '--version-info', str(binary)], env=env).decode()
    glibc = re.findall(r'\bGLIBC_(\d+(?:\.\d+)+)\b', versions)
    if not glibc:
        raise RuntimeError('Cannot determine the executable glibc requirement')
    minimum_glibc = max(glibc, key=version_tuple)
    # The reviewed binary uses GCC 5-era C++ symbol versions. Fail closed after
    # a toolchain change rather than silently publish inadequate dependencies.
    for namespace, maximum in (('GLIBCXX', '3.4.21'), ('CXXABI', '1.3.9')):
        found = re.findall(r'\b' + namespace + r'_(\d+(?:\.\d+)+)\b', versions)
        if found and max(map(version_tuple, found)) > version_tuple(maximum):
            raise RuntimeError(f'Review the libstdc++6 dependency for new {namespace} symbol versions')
    dependencies = [f'libc6 (>= {minimum_glibc})']
    for name in needed:
        dependency = NEEDED_PACKAGES[name]
        if dependency and dependency not in dependencies:
            dependencies.append(dependency)
    dependencies.append('python3 (>= 3.8)')
    return needed, ', '.join(dependencies)


def png_dimensions(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR':
        raise RuntimeError('The app icon is not a PNG image')
    return struct.unpack('!II', data[16:24])


def payload_files():
    files = [
        ('dist/flipper-one-remote', APP + '/flipper-one-remote', 0o755),
        ('main/bridge.py', APP + '/bridge.py', 0o644),
        ('run-flipper-one-remote', BASE + '/bin/flipper-one-remote', 0o755),
        ('applications/flipper-one-remote.desktop', BASE + '/applications/flipper-one-remote.desktop', 0o644),
        ('share/images/flipper-one-remote.png', BASE + '/share/images/flipper-one-remote.png', 0o644),
        ('LICENSE', APP + '/LICENSE', 0o644),
        ('share/images/ICON_LICENSE.txt', APP + '/ICON_LICENSE.txt', 0o644),
    ]
    notices = sorted((ROOT / 'share/licenses').iterdir())
    if not notices:
        raise RuntimeError('Third-party license notices are missing')
    for notice in notices:
        if not notice.is_file() or notice.is_symlink():
            raise RuntimeError('Expected a regular license notice: ' + str(notice))
        files.append((notice.relative_to(ROOT).as_posix(), APP + '/licenses/' + notice.name, 0o644))
    payload = {}
    for source_name, target_name, mode in files:
        source = ROOT / source_name
        if not source.is_file() or source.is_symlink() or ROOT not in source.resolve().parents:
            raise RuntimeError('Expected a regular project input: ' + source_name)
        payload[target_name] = (source.read_bytes(), mode)
    normalized_package = re.sub(r'[-_.]', '', PACKAGE).lower()
    shared_paths = (BASE + '/apps/', BASE + '/bin/',
                    BASE + '/applications/', BASE + '/share/images/')
    for name in payload:
        for shared in shared_paths:
            if name.startswith(shared):
                entry = name[len(shared):].split('/', 1)[0]
                if not re.sub(r'[-_.]', '', entry).lower().startswith(normalized_package):
                    raise RuntimeError('Shared APPLaunch path must start with the package name: ' + name)
    desktop_name = BASE + '/applications/flipper-one-remote.desktop'
    desktop = payload[desktop_name][0].decode('utf-8')
    if 'Exec=bin/flipper-one-remote' not in desktop.splitlines():
        raise RuntimeError('Desktop entry must launch the packaged bin/flipper-one-remote')
    icon_name = BASE + '/share/images/flipper-one-remote.png'
    if 'Icon=share/images/flipper-one-remote.png' not in desktop.splitlines():
        raise RuntimeError('Desktop entry must reference the packaged app icon')
    if png_dimensions(payload[icon_name][0]) != (256, 256):
        raise RuntimeError('Expected the reviewed 256x256 APPLaunch icon')
    copyright_text = f'''FlipCTL for CardputerZero
Project: {HOMEPAGE}
Maintainer: {MAINTAINER}

Original project code and pixel artwork: GNU GPL version 3 only
(SPDX: GPL-3.0-only). The complete license is installed at
/usr/share/APPLaunch/apps/{PACKAGE}/LICENSE and is also available on
Debian systems at /usr/share/common-licenses/GPL-3.

The app icon is derived from Flipper Android App artwork.
Copyright (c) 2020 Flipper Zero; MIT license. The complete upstream notice
is installed at /usr/share/APPLaunch/apps/{PACKAGE}/ICON_LICENSE.txt.

Statically linked LVGL code, Montserrat and FontAwesome fonts, and LodePNG
retain their upstream licenses and copyright notices. Their complete notices
and inventory are installed under
/usr/share/APPLaunch/apps/{PACKAGE}/licenses/.

Distribute this executable with its matching complete corresponding source,
including the actual LVGL source, configuration and build scripts. System
shared libraries are dependencies and are not bundled in this package.
'''
    payload['usr/share/doc/' + PACKAGE + '/copyright'] = (copyright_text.encode(), 0o644)
    readme = '''FlipCTL Debian package

This package targets the CardputerZero arm64 environment with APPLaunch,
a readable/writable framebuffer, and a readable evdev keyboard. It installs
only application files under /usr/share/APPLaunch and license documentation.
It does not create users, alter device permissions, run privileged helpers,
install services, or restart APPLaunch during installation or removal.

Install using apt so runtime dependencies can be resolved. After installation,
restart APPLaunch in your existing user session if its app list is cached.
'''
    payload['usr/share/doc/' + PACKAGE + '/README.Debian'] = (readme.encode(), 0o644)
    return payload


def write_file(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)


def inspect_package(package, payload, dpkg, env, expected_control):
    actual = run([dpkg, '--field', str(package)], env=env).decode()
    if actual != expected_control:
        raise RuntimeError('Packaged control fields differ from the expected metadata')
    data_tar = run([dpkg, '--fsys-tarfile', str(package)], env=env)
    found = {}
    with tarfile.open(fileobj=io.BytesIO(data_tar), mode='r:') as archive:
        for member in archive.getmembers():
            name = (member.name[2:] if member.name.startswith('./') else member.name).rstrip('/')
            if member.uid != 0 or member.gid != 0:
                raise RuntimeError('Package entry is not owned by root: ' + name)
            if member.isdir():
                if member.mode != 0o755:
                    raise RuntimeError('Unexpected directory mode: ' + name)
                continue
            if not member.isfile() or name not in payload:
                raise RuntimeError('Unexpected package entry: ' + name)
            expected_data, expected_mode = payload[name]
            data = archive.extractfile(member).read()
            if data != expected_data or member.mode != expected_mode:
                raise RuntimeError('Packaged file bytes or permissions differ: ' + name)
            found[name] = data
    if set(found) != set(payload):
        raise RuntimeError('Package file inventory is incomplete')
    control_tar = run([dpkg, '--ctrl-tarfile', str(package)], env=env)
    with tarfile.open(fileobj=io.BytesIO(control_tar), mode='r:') as archive:
        names = {(entry.name[2:] if entry.name.startswith('./') else entry.name)
                 for entry in archive if entry.isfile()}
        if names != {'control', 'md5sums'}:
            raise RuntimeError('Unexpected package control files or maintainer scripts')
    return actual


def main():
    dpkg = find_tool(['dpkg-deb'])
    readelf = find_tool([os.environ.get('READELF', 'aarch64-linux-gnu-readelf'), 'readelf'])
    epoch_text = os.environ.get('SOURCE_DATE_EPOCH', '0')
    if not epoch_text.isdigit():
        raise RuntimeError('SOURCE_DATE_EPOCH must be a nonnegative integer')
    epoch = int(epoch_text)
    env = dict(os.environ, SOURCE_DATE_EPOCH=str(epoch), LC_ALL='C', TZ='UTC')
    binary = ROOT / 'dist/flipper-one-remote'
    needed, dependencies = elf_dependencies(binary, readelf, env)
    payload = payload_files()
    installed_size = math.ceil(sum(len(data) for data, _ in payload.values()) / 1024)
    control = f'''Package: {PACKAGE}
Version: {VERSION}
Architecture: {ARCH}
Maintainer: {MAINTAINER}
Section: utils
Priority: optional
Homepage: {HOMEPAGE}
Depends: {dependencies}
Installed-Size: {installed_size}
Description: Control Flipper One from CardputerZero over Ethernet or WiFi
 Display the remote grayscale screen on CardputerZero's 320x170 display.
 Includes automatic wired connection, editable WiFi fallback, device-keyboard
 controls, and a pixel-art key guide on H.
'''
    destination = ROOT / 'dist' / OUTPUT_NAME
    expected_destination = ROOT.resolve() / 'dist' / OUTPUT_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.resolve() != expected_destination:
        raise RuntimeError('Refusing an unexpected package output path')
    with tempfile.TemporaryDirectory(prefix='.deb-build-', dir=destination.parent) as folder:
        work = Path(folder).resolve()
        stage = work / 'root'
        stage.mkdir(mode=0o755)
        for name, (data, mode) in sorted(payload.items()):
            write_file(stage / name, data, mode)
        write_file(stage / 'DEBIAN/control', control.encode(), 0o644)
        sums = ''.join(hashlib.md5(data).hexdigest() + '  ' + name + '\n'
                       for name, (data, _) in sorted(payload.items()))
        write_file(stage / 'DEBIAN/md5sums', sums.encode(), 0o644)
        for path in sorted(stage.rglob('*')):
            if path.is_dir():
                path.chmod(0o755)
            os.utime(path, (epoch, epoch))
        os.utime(stage, (epoch, epoch))
        built = work / OUTPUT_NAME
        run([dpkg, '--root-owner-group', '--uniform-compression', '-Zgzip', '-z9',
             '--threads-max=1', '--build', str(stage), str(built)], env=env)
        actual_control = inspect_package(built, payload, dpkg, env, control)
        # Validate both resolved paths immediately before atomic replacement.
        if built.resolve().parent != work or destination.resolve() != expected_destination:
            raise RuntimeError('Refusing an unexpected package replacement path')
        os.replace(built, destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    checksum = destination.with_suffix('.deb.sha256')
    if checksum.resolve() != expected_destination.with_suffix('.deb.sha256'):
        raise RuntimeError('Refusing an unexpected checksum output path')
    checksum.write_text(digest + '  ' + destination.name + '\n')
    checksum.chmod(0o644)
    destination.chmod(0o644)
    print(actual_control, end='')
    print('ELF NEEDED: ' + ', '.join(needed))
    print(f'Validated {len(payload)} files, root ownership, modes, binary bytes, and 256x256 icon')
    print('Binary SHA-256: ' + hashlib.sha256(payload[APP + '/flipper-one-remote'][0]).hexdigest())
    print('Icon SHA-256: ' + hashlib.sha256(payload[BASE + '/share/images/flipper-one-remote.png'][0]).hexdigest())
    print('Package SHA-256: ' + digest)
    print(destination)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr.decode(errors='replace'), end='', file=__import__('sys').stderr)
        raise SystemExit(str(exc))
