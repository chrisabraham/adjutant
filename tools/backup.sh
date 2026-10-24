#!/usr/bin/env bash
# Encrypted backup of the Adjutant database, with a restore test every time.
#
# Pattern 9. An encrypted nightly backup with a tested restore.
#
#   tools/backup.sh            make a backup, prove it restores, keep the newest $KEEP
#   tools/backup.sh --restore FILE.gpg DEST.sqlite3
#
# Needs: python3, gpg. The passphrase is a file you create once, outside any repo:
#   umask 077; head -c 32 /dev/urandom | base64 > ~/.config/adjutant/backup-passphrase
# Keep a copy of that passphrase somewhere safe (a password manager). Without it the
# backups are noise.
#
# Off-machine copy: set ADJUTANT_BACKUP_REPO to a clone of a PRIVATE git repo; each
# backup is committed and pushed there. The file is encrypted before it leaves.
#
# Nightly with cron:  30 3 * * *  /path/to/adjutant/tools/backup.sh >> ~/.local/share/adjutant/backup.log 2>&1
set -euo pipefail

CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/adjutant"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}/adjutant"
PASS="$CONFIG/backup-passphrase"
OUT="$DATA/backups"
KEEP="${ADJUTANT_BACKUP_KEEP:-14}"

die() { echo "backup: $*" >&2; exit 1; }
[ -s "$PASS" ] || die "no passphrase at $PASS (see the top of this script)"
command -v gpg >/dev/null || die "gpg is not installed"

decrypt() {  # decrypt FILE.gpg DEST
    gpg --batch --quiet --yes --pinentry-mode loopback --passphrase-file "$PASS" --decrypt --output "$2" "$1"
}

if [ "${1:-}" = "--restore" ]; then
    [ $# -eq 3 ] || die "usage: backup.sh --restore FILE.gpg DEST.sqlite3"
    [ -e "$3" ] && die "$3 exists; restore to a new path, then move it into place yourself"
    decrypt "$2" "$3"
    echo "Restored to $3"
    exit 0
fi

[ -f "$DATA/adjutant.sqlite3" ] || die "no database at $DATA/adjutant.sqlite3"
mkdir -p "$OUT"; chmod 700 "$OUT"
STAMP="$(date +%Y%m%d-%H%M%S)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

# A consistent copy even while Adjutant is running.
python3 - "$DATA/adjutant.sqlite3" "$WORK/copy.sqlite3" <<'PY'
import sqlite3, sys
source, target = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
source.backup(target)
target.close()
PY

FILE="$OUT/adjutant-$STAMP.sqlite3.gpg"
gpg --batch --quiet --yes --pinentry-mode loopback --passphrase-file "$PASS" \
    --symmetric --cipher-algo AES256 --output "$FILE" "$WORK/copy.sqlite3"

# The restore test: a backup that hasn't been restored isn't a backup.
decrypt "$FILE" "$WORK/restored.sqlite3"
CHECK="$(python3 -c 'import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute("PRAGMA integrity_check").fetchone()[0])' "$WORK/restored.sqlite3")"
[ "$CHECK" = "ok" ] || die "restore test FAILED for $FILE ($CHECK)"
cmp -s "$WORK/copy.sqlite3" "$WORK/restored.sqlite3" || die "restore test FAILED: restored copy differs"

ls -1t "$OUT"/adjutant-*.sqlite3.gpg | tail -n +"$((KEEP + 1))" | xargs -r rm --
echo "$(date -Iseconds) OK $FILE (restore tested)"

if [ -n "${ADJUTANT_BACKUP_REPO:-}" ]; then
    cp "$FILE" "$ADJUTANT_BACKUP_REPO/"
    ls -1t "$ADJUTANT_BACKUP_REPO"/adjutant-*.sqlite3.gpg | tail -n +"$((KEEP + 1))" | xargs -r git -C "$ADJUTANT_BACKUP_REPO" rm -q --
    git -C "$ADJUTANT_BACKUP_REPO" add -A
    git -C "$ADJUTANT_BACKUP_REPO" commit -q -m "Backup $STAMP" && git -C "$ADJUTANT_BACKUP_REPO" push -q
    echo "$(date -Iseconds) pushed to $ADJUTANT_BACKUP_REPO"
fi
