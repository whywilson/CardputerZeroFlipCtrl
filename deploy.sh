#!/bin/sh
set -eu
cd "$(dirname "$0")"
TARGET=${1:-pi@cardputerzero.local}
# Use SSH keys or set SSHPASS; an alternate pinned host key file is optional.
KNOWN_HOSTS=${SSH_KNOWN_HOSTS_FILE:-$HOME/.ssh/known_hosts}
remote() { if [ -n "${SSHPASS:-}" ]; then sshpass -e ssh -o UserKnownHostsFile="$KNOWN_HOSTS" -o StrictHostKeyChecking=yes "$TARGET" "$@"; else ssh -o UserKnownHostsFile="$KNOWN_HOSTS" -o StrictHostKeyChecking=yes "$TARGET" "$@"; fi; }
copy() { if [ -n "${SSHPASS:-}" ]; then sshpass -e scp -o UserKnownHostsFile="$KNOWN_HOSTS" -o StrictHostKeyChecking=yes "$@" "$TARGET:/tmp/flipper-one-remote-deploy/"; else scp -o UserKnownHostsFile="$KNOWN_HOSTS" -o StrictHostKeyChecking=yes "$@" "$TARGET:/tmp/flipper-one-remote-deploy/"; fi; }
remote 'mkdir -p /tmp/flipper-one-remote-deploy'
copy install.sh dist/flipper-one-remote main/bridge.py run-flipper-one-remote applications/flipper-one-remote.desktop share/images/flipper-one-remote.png LICENSE share/images/ICON_LICENSE.txt
copy -r share/licenses
if remote 'sudo -n true' 2>/dev/null; then
  remote 'sudo -n sh /tmp/flipper-one-remote-deploy/install.sh'
elif [ -n "${SUDO_PASSWORD:-${SSHPASS:-}}" ]; then
  printf '%s\n' "${SUDO_PASSWORD:-$SSHPASS}" | remote 'sudo -S sh /tmp/flipper-one-remote-deploy/install.sh'
else
  echo 'sudo requires a password; set SUDO_PASSWORD' >&2
  exit 1
fi
remote 'systemctl --user restart APPLaunch.service'
