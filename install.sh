#!/bin/sh
set -eu
STAGE=/tmp/flipper-one-remote-deploy
BASE=/usr/share/APPLaunch
mkdir -p "$BASE/apps/flipper-one-remote/licenses" "$BASE/bin" "$BASE/applications" "$BASE/share/images"
install -m755 "$STAGE/flipper-one-remote" "$BASE/apps/flipper-one-remote/flipper-one-remote.next"
mv "$BASE/apps/flipper-one-remote/flipper-one-remote.next" "$BASE/apps/flipper-one-remote/flipper-one-remote"
install -m644 "$STAGE/bridge.py" "$BASE/apps/flipper-one-remote/"
install -m644 "$STAGE/LICENSE" "$BASE/apps/flipper-one-remote/"
install -m644 "$STAGE/ICON_LICENSE.txt" "$BASE/apps/flipper-one-remote/"
install -m644 "$STAGE/licenses/"* "$BASE/apps/flipper-one-remote/licenses/"
install -m755 "$STAGE/run-flipper-one-remote" "$BASE/bin/flipper-one-remote"
install -m644 "$STAGE/flipper-one-remote.desktop" "$BASE/applications/"
install -m644 "$STAGE/flipper-one-remote.png" "$BASE/share/images/"
