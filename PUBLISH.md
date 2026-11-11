# Application Store Publish Record

Source publication and store submission are tracked separately. The user has authorized pushing the source and submitting this release to Cardputer.cc.

Portal: <https://dev.cardputer.cc/#/upload>

## Package

- Debian package path: `dist/flipper-one-remote_0.1.0_arm64.deb`
- Package: `flipper-one-remote`
- Version: `0.1.0`
- Architecture: `arm64`
- Maintainer: `Wilson <15230131+whywilson@users.noreply.github.com>`
- Minimum runtime: glibc 2.38; tested device uses glibc 2.41.
- APPLaunch desktop path: `/usr/share/APPLaunch/applications/flipper-one-remote.desktop`
- Executable path: `/usr/share/APPLaunch/bin/flipper-one-remote`
- Package SHA-256: `d694d36dcef063451e68295dcee96b9846c41a7af27c2ac446add3a44bdaf69b`

## Source and Ownership

- Public source repository: <https://github.com/whywilson/CardputerZeroFlipCtrl>
- GitHub uploader/owner: `whywilson`
- Uploader contact: GitHub noreply address only; no personal email in public metadata.
- Corresponding source: `dist/flipctl-source.tar.gz`, to accompany the executable release.

## Listing

- Application name: `FlipCTL`
- Summary: Control Flipper One over Ethernet or WiFi from CardputerZero
- Description, permissions, screenshots and icon: `app-builder.json` store section.
- Categories: `Hardware & IoT`, `System Tools`
- Share code: `FLIP`
- Declared requirements: network access and additional Flipper One hardware.
- License: `GPL-3.0-only`, with the bundled third-party notices retained.

## Assets

- Source icon: `share/images/flipper-one-remote.png` (256 x 256).
- Packaged icon: `/usr/share/APPLaunch/share/images/flipper-one-remote.png`.
- Screenshot 1: `docs/screenshots/connection-auto.png` (320 x 170).
- Screenshot 2: `docs/screenshots/connection-wifi.png` (320 x 170).
- Screenshot 3: `docs/screenshots/key-guide.png` (320 x 170).
- Screenshot 4: `docs/screenshots/invalid-ip.png` (320 x 170).
- Optional screenshots 5 and 6: not used.

## Preflight

- [x] `.deb` exists and can be parsed; gzip control/data archives and root ownership verified.
- [x] Control fields contain Package, Version, Architecture, Maintainer, Depends and Homepage.
- [x] All native executable payloads are AArch64; runtime dependencies match ELF requirements.
- [x] APPLaunch desktop entry, executable, PNG icon, and license notices are included.
- [x] Shared installation paths use the package-name prefix.
- [x] Two independent package builds are byte-for-byte identical.
- [x] Public registry has no conflicting package name, title or share code at preflight time.
- [x] Four clean 320 x 170 screenshots and a 256 x 256 icon exist.
- [x] Public source and selected screenshots have been checked for credentials and private device details.
- [x] The user explicitly approved source push and external store submission.

## Submission Result

- Status: `submitted; all automated checks passed; awaiting first-release maintainer review`
- Submission route: official `czdev` preflight and buffer-release flow; recovered its local Git fetch failure with GitHub's Git Data API.
- Submitted at: `2026-11-11T19:56:34Z` (`2026-11-12 03:56:34 Asia/Shanghai`).
- GitHub source release: <https://github.com/whywilson/CardputerZeroFlipCtrl/releases/tag/v0.1.0>
- Source revision: `92ad31d` (release `v0.1.0`).
- Complete source archive SHA-256: `8cb9345c3fe09992438ec61ad9d781b81813b991a4c00905fde7d3f07a67140f`.
- Passing validation: <https://github.com/CardputerZero/packages/actions/runs/43092322917>
- Passing staging capture: <https://github.com/CardputerZero/packages/actions/runs/43092318889>
- Validation report: <https://github.com/CardputerZero/packages/pull/267#issuecomment-6805938822>
- Tracking pull request: <https://github.com/CardputerZero/packages/pull/267>
- Required real-device demo: <https://github.com/CardputerZero/packages/pull/267#issuecomment-6805878225>
- Demo is a real-device framebuffer recording, not a physical-camera recording.
- Additional user-provided review material: <https://x.com/mtoolstec/status/2120067252976586806>.
- Review-reference comment: <https://github.com/CardputerZero/packages/pull/267#issuecomment-6805937285>.
- Validated package metadata commit: `33af2a29f3bf08806686faf09689961e79071e84` in the contributor fork.
- The first validation was superseded after merging the current store index; it had incorrectly included a concurrently updated, unrelated package in its ownership check.
- First-release policy: a maintainer reviews a short real-device demo before merging; validation alone does not make a new app live.
