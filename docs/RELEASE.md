# Source and binary releases

## Scope

Project code and original pixel artwork use GPL-3.0-only. Reviewed public screenshots are in `docs/screenshots/`. This document covers reproducible source releases. App-store packages, maintainer identity, and external submissions are tracked separately in `PUBLISH.md`. Version 0.1.0 is available on GitHub; its store submission has passed automated validation and awaits first-release maintainer review.

## Build inputs

- An AArch64 Linux GNU C/C++ toolchain and GNU ar, plus Python 3.8 or later.
- A device-compatible AArch64 sysroot with standard C/C++ headers, dynamic libraries, and FreeType, libpng, and zlib development files. The sysroot is a build-environment dependency and is not included in the source archive.
- The actual LVGL 9.5 development source tree. The original SDK's `lvgl_component/SConstruct` specifies commit `85aa60d18b3d5e5588d7b247abf90198f07c8a63` from dianjixz/lvgl. The complete source archive includes the actual local sources and per-file SHA-256 checksums, including local changes. A version label alone is not a substitute for these sources.
- `config/lvgl_config.h` includes every actual `CONFIG_LV*` setting, with unrelated toolchain settings and local machine paths removed. Third-party notices are in `share/licenses/`.

`build.sh` calls `tools/build_lvgl.py` to compile C, C++, and assembly files under LVGL's `src/`, then links the client. It does not require another app's prebuilt archive. LVGL examples and demos are not linked into this client. File-prefix mapping keeps local user-directory paths out of the executable.

From an extracted complete source archive:

```sh
sha256sum -c SOURCE-SHA256SUMS
export LVGL_SYSROOT=/path/to/aarch64-sysroot
sh build.sh
python3 tests/test_protocol.py
c++ -std=c++17 tests/scaler_test.cpp -o /tmp/flipctl-scaler-test
/tmp/flipctl-scaler-test
```

On macOS, use `shasum -a 256 -c SOURCE-SHA256SUMS` for verification. Set `CC`, `CXX`, and `AR` if the cross-compilation tools are not in PATH. A regular Git checkout excludes the large LVGL dependency tree; set `LVGL_INCLUDE_DIR` to the parent directory containing `lvgl/lvgl.h`.

## Create a complete source archive

```sh
python3 tools/package_source.py --lvgl /path/to/actual/lvgl
```

The default outputs are `dist/flipctl-source.tar.gz` and its `.sha256` checksum file. The archive includes:

- Public project sources, build and installation scripts, tests, licenses, documentation, reviewed screenshots, and the original key-guide artwork and generator.
- The actual LVGL implementation sources, upstream build and font-generation scripts, original font assets, and licenses under `third_party/lvgl/`. Unlinked upstream demos, examples, and test fixtures are excluded.
- `SOURCE-SHA256SUMS`, containing checksums for every archived input file.

The packager uses directory and file-type allowlists. It excludes historical `dist/` contents, raw device captures, bytecode, logs, and build caches, and removes local user/group ownership metadata. Do not publish an archive of the entire working directory. The source package contains no prebuilt executable, sysroot, or login credentials.

## Distribute an executable

Provide the complete corresponding source archive alongside each executable release: project sources, actual LVGL sources, configuration, and build scripts. Do not substitute sources from another dependency version. Retain the project GPL, icon MIT, LVGL MIT, Montserrat / FontAwesome OFL, and LodePNG notices. The installation script installs these notices with the app.

Installing a copy of LICENSE does not replace the GPL's source-availability requirements. Device system packages supply the dynamic libraries; if you redistribute those libraries separately, address their own license and source requirements. This source archive does not include those libraries.

## Validation

- All 531 LVGL source files were cross-compiled from source, and the AArch64 client linked successfully.
- The 11 Python protocol tests, C++ scaler tests, Python compilation checks, and shell syntax checks passed.
- Device checks covered the H key guide, dismissal controls, and connection-page input. Original test captures used an isolated configuration; the current listing also includes developer-approved connected remote screens. See the screenshot notes for provenance.
- Public source candidates were checked for credentials, local absolute paths, and actual private device addresses. The documented product Ethernet default, `192.168.50.2`, is intentionally retained.

Local verification does not itself publish a release. The current publication record is:

- [Source repository](https://github.com/whywilson/CardputerZeroFlipCtrl).
- [GitHub release v0.1.0](https://github.com/whywilson/CardputerZeroFlipCtrl/releases/tag/v0.1.0), from source revision `92ad31d`, with the Debian package, complete corresponding source, checksums, and a real-device framebuffer demo.
- [CardputerZero store submission PR #269](https://github.com/CardputerZero/packages/pull/269): both automated checks passed; first-release maintainer review is pending. The old PR #267 is closed and superseded.
- [Real-hardware demonstration for review](https://x.com/mtoolstec/status/2120067252976586806).

The release archive corresponds to the tagged implementation; later publication-record documentation changes do not replace the released implementation or its immutable assets.
