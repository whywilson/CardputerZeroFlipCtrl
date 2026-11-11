#!/bin/sh
set -eu
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
RFID="$ROOT/projects/RFID"
SDK="$ROOT/SDK"
# Defaults support this demo monorepo; override these for a standalone checkout.
LVGL_SYSROOT=${LVGL_SYSROOT:-$RFID/build/static_lib}
if [ -f third_party/lvgl/lvgl.h ]; then
    DEFAULT_LVGL_INCLUDE_DIR="$PWD/third_party"
else
    DEFAULT_LVGL_INCLUDE_DIR="$SDK/github_source/lvgl/lvgl_9_5"
fi
LVGL_INCLUDE_DIR=${LVGL_INCLUDE_DIR:-$DEFAULT_LVGL_INCLUDE_DIR}
LVGL_CONFIG_HEADER=${LVGL_CONFIG_HEADER:-$PWD/config/lvgl_config.h}
BUILD_LVGL=0
if [ -z "${LVGL_STATIC_LIBRARY:-}" ]; then
    LVGL_STATIC_LIBRARY="$PWD/dist/lvgl/liblvgl.a"
    BUILD_LVGL=1
fi
if [ -z "${CXX:-}" ]; then
    if command -v aarch64-linux-gnu-g++ >/dev/null 2>&1; then
        CXX=aarch64-linux-gnu-g++
    elif [ -x /opt/homebrew/bin/aarch64-linux-gnu-g++ ]; then
        CXX=/opt/homebrew/bin/aarch64-linux-gnu-g++
    else
        echo 'AArch64 GNU C++ compiler missing; set CXX to its executable.' >&2
        exit 1
    fi
fi
for prerequisite in "$LVGL_SYSROOT/usr/include/aarch64-linux-gnu" "$LVGL_INCLUDE_DIR/lvgl/lvgl.h" "$LVGL_CONFIG_HEADER"; do
    if [ ! -e "$prerequisite" ]; then
        echo "Missing build prerequisite: $prerequisite" >&2
        echo 'Set LVGL_SYSROOT, LVGL_INCLUDE_DIR, LVGL_CONFIG_HEADER and LVGL_STATIC_LIBRARY; see README.md.' >&2
        exit 1
    fi
done
if [ "$BUILD_LVGL" = 1 ]; then
    export LVGL_SYSROOT LVGL_INCLUDE_DIR LVGL_CONFIG_HEADER CXX
    python3 tools/build_lvgl.py
fi
if [ ! -f "$LVGL_STATIC_LIBRARY" ]; then
    echo "LVGL archive missing: $LVGL_STATIC_LIBRARY" >&2
    exit 1
fi
mkdir -p dist
"$CXX" -O2 -std=c++17 -ffile-prefix-map="$PWD"=. -I"$LVGL_SYSROOT/usr/include/aarch64-linux-gnu" -DLV_CONF_SKIP -include "$LVGL_CONFIG_HEADER" -I"$LVGL_INCLUDE_DIR" --sysroot="$LVGL_SYSROOT" main/main.cpp "$LVGL_STATIC_LIBRARY" -L"$LVGL_SYSROOT/usr/lib/aarch64-linux-gnu" -B"$LVGL_SYSROOT/usr/lib/aarch64-linux-gnu/" -Wl,--gc-sections -Wl,-rpath-link,"$LVGL_SYSROOT/usr/lib/aarch64-linux-gnu" -Wl,-rpath-link,"$LVGL_SYSROOT/lib/aarch64-linux-gnu" -lfreetype -lpng16 -lz -lm -lpthread -o dist/flipper-one-remote
