#!/usr/bin/env python3
r"""Rebuild local LVGL sources for AArch64 Linux without a prebuilt archive.

Usage (from any directory; environment paths are relative to that directory):
    LVGL_INCLUDE_DIR=/path/to/parent/of/lvgl \
    LVGL_SYSROOT=/path/to/aarch64/sysroot python3 tools/build_lvgl.py

LVGL_CONFIG_HEADER defaults to this project's config/lvgl_config.h.
CC, CXX and AR accept executable names/paths (and shell-quoted arguments).
Otherwise aarch64-linux-gnu tools are found in PATH or Homebrew's bin dirs.
No shell, download, external Python package, or sibling archive is used.
The archive is always written to this project's dist/lvgl/liblvgl.a.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile


PROJECT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT / "dist" / "lvgl" / "liblvgl.a"


class BuildError(Exception):
    pass


def tool(variable, fallback):
    value = os.environ.get(variable)
    if value:
        command = shlex.split(value)
        if not command or not shutil.which(command[0]):
            raise BuildError(f"{variable} executable not found: {value}")
        return command
    candidates = [fallback, f"/opt/homebrew/bin/{fallback}", f"/usr/local/bin/{fallback}"]
    for candidate in candidates:
        executable = shutil.which(candidate)
        if executable:
            return [executable]
    raise BuildError(f"Missing {fallback}; install an AArch64 GNU toolchain or set {variable}.")


def run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # Preserve complete compiler diagnostics, including the original stderr.
        print(f"Command failed ({result.returncode}): {shlex.join(command)}", file=sys.stderr)
        sys.stdout.flush()
        if result.stdout:
            sys.stderr.buffer.write(result.stdout)
        if result.stderr:
            sys.stderr.buffer.write(result.stderr)
        sys.stderr.flush()
        raise BuildError("See command diagnostics above.")
    return result


def environment_path(name):
    value = os.environ.get(name)
    if not value:
        raise BuildError(f"Set {name}; run with --help for usage.")
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise BuildError(f"{name} is not a directory: {path}")
    return path


def build(jobs):
    include = environment_path("LVGL_INCLUDE_DIR")
    sysroot = environment_path("LVGL_SYSROOT")
    source_root = include / "lvgl"
    for relative in ("lvgl.h", "src/lv_conf_internal.h"):
        if not (source_root / relative).is_file():
            raise BuildError(f"Missing {source_root / relative}; LVGL_INCLUDE_DIR must contain lvgl/lvgl.h.")
    config = Path(os.environ.get("LVGL_CONFIG_HEADER", PROJECT / "config/lvgl_config.h")).expanduser().resolve()
    if not config.is_file():
        raise BuildError(f"LVGL configuration header not found: {config}")
    if not (sysroot / "usr/include").is_dir():
        raise BuildError(f"Missing sysroot headers: {sysroot / 'usr/include'}")

    # Match LVGL's source library: src/**/*.c, src/**/*.cpp, src/**/*.S.
    # Feature guards in LVGL select enabled implementations, including NEON.
    # Examples and demos are separate upstream targets and are not in liblvgl.
    sources = sorted(path for path in (source_root / "src").rglob("*")
                     if path.is_file() and path.suffix in (".c", ".cpp", ".S", ".s"))
    if not sources:
        raise BuildError(f"No LVGL sources found in {source_root / 'src'}")
    cc = tool("CC", "aarch64-linux-gnu-gcc")
    cxx = tool("CXX", "aarch64-linux-gnu-g++") if any(p.suffix == ".cpp" for p in sources) else cc
    ar = tool("AR", "aarch64-linux-gnu-ar")
    targets = [run(compiler + ["-dumpmachine"]).stdout.decode().strip()
               for compiler in (cc, cxx)]
    if any(not target.startswith("aarch64") or "linux" not in target for target in targets):
        raise BuildError(f"CC and CXX must target AArch64 Linux; got {targets}")

    common = ["-O2", "-ffunction-sections", "-fdata-sections",
              f"-ffile-prefix-map={source_root}=lvgl", f"-ffile-prefix-map={PROJECT}=.",
              "-DLV_CONF_SKIP",
              "-include", str(config), "-I", str(include), "-I", str(source_root),
              f"--sysroot={sysroot}"]
    # Debian-style sysroots need their architecture-specific libc headers.
    multiarch = sysroot / "usr/include/aarch64-linux-gnu"
    if multiarch.is_dir():
        common += ["-I", str(multiarch)]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"LVGL source: {source_root}\nConfiguration: {config}\nTarget: {targets[0]}", flush=True)
    print(f"Compiling {len(sources)} sources with {jobs} workers...", flush=True)
    # A fresh temporary object directory prevents stale objects after source or
    # configuration changes; publish only a complete, indexed archive.
    with tempfile.TemporaryDirectory(prefix=".build-", dir=OUTPUT.parent) as temporary:
        work = Path(temporary).resolve()
        objects = [work / f"{index:05d}_{source.stem}.o" for index, source in enumerate(sources)]

        def compile_one(index):
            source = sources[index]
            compiler = cxx if source.suffix == ".cpp" else cc
            standard = ["-std=c++17"] if source.suffix == ".cpp" else ["-std=gnu99"] if source.suffix == ".c" else []
            # Return diagnostics to the main thread so failures do not interleave.
            command = compiler + common + standard + ["-c", str(source), "-o", str(objects[index])]
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return source, command, result

        failures = 0
        diagnostics = set()
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            pending = [executor.submit(compile_one, index) for index in range(len(sources))]
            completed = 0
            for future in as_completed(pending):
                if future.cancelled():
                    continue
                source, command, result = future.result()
                completed += 1
                if result.returncode:
                    failures += 1
                    print(f"Compile failed ({result.returncode}): {source.relative_to(source_root)}", file=sys.stderr)
                    print(shlex.join(command), file=sys.stderr)
                    sys.stderr.flush()
                    if result.stdout:
                        sys.stderr.buffer.write(result.stdout)
                    if result.stderr:
                        sys.stderr.buffer.write(result.stderr)
                    sys.stderr.flush()
                    for queued in pending:
                        queued.cancel()
                elif result.stderr:
                    diagnostics.add(result.stderr)
                if completed % 100 == 0:
                    print(f"Compiled {completed}/{len(sources)}", flush=True)
        for diagnostic in sorted(diagnostics):
            sys.stderr.buffer.write(diagnostic)
        sys.stderr.flush()
        if failures:
            raise BuildError(f"{failures} compilation(s) failed; existing archive was not replaced.")

        archive = work / "liblvgl.a"
        # Batch archive arguments to stay below platform command-line limits.
        for start in range(0, len(objects), 100):
            run(ar + ["rcs", str(archive)] + [str(obj) for obj in objects[start:start + 100]])
        # Check both resolved paths immediately before the atomic replacement.
        destination = OUTPUT.resolve()
        if archive.resolve().parent != work or destination.parent != OUTPUT.parent.resolve():
            raise BuildError("Unexpected archive destination; refusing to replace it.")
        os.replace(archive, destination)
    print(f"Built {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jobs", type=int, choices=range(1, 5), default=4,
                        help="parallel compiler processes, 1 to 4 (default: 4)")
    args = parser.parse_args()
    try:
        build(args.jobs)
    except (BuildError, OSError, ValueError) as error:
        print(f"LVGL build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
