#!/usr/bin/env bash
# Publish this course only. Release directory + rollback; no fixed /tmp collisions.
# Requires ssh alias pxhome, pct, nginx and a separately configured NPM HTTPS host.
set -euo pipefail
CTID="${CTID:-109}"
SSH_HOST="${SSH_HOST:-pxhome}"
SITE_DIR="${SITE_DIR:-ai-engineering.adelfos.ru}"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
[[ "$CTID" =~ ^[0-9]+$ ]] || { echo 'Invalid CTID' >&2; exit 2; }
[[ "$SITE_DIR" =~ ^[a-z0-9]+([.-][a-z0-9]+)+$ ]] || { echo 'Invalid SITE_DIR' >&2; exit 2; }
STAGE=$(mktemp -d -t ai-engineering.XXXXXXXX)
REMOTE_STAGE=''
cleanup() {
  rm -rf -- "$STAGE"
  if [[ -n "$REMOTE_STAGE" ]]; then
    ssh "$SSH_HOST" "rm -rf -- '$REMOTE_STAGE'" || true
  fi
}
trap cleanup EXIT
cd "$ROOT_DIR"
python3 scripts/check_project.py
python3 scripts/build_site.py "$STAGE/site"
if [[ "${1:-}" == '--build-only' ]]; then
  [[ -n "${BUILD_DIR:-}" && ! -e "$BUILD_DIR" ]] || { echo 'Set BUILD_DIR to a new output directory' >&2; exit 2; }
  cp -r "$STAGE/site" "$BUILD_DIR"
  echo "Built $BUILD_DIR; nothing deployed."
  exit 0
fi
[[ $# == 0 ]] || { echo 'Usage: ./deploy-pxhome.sh [--build-only]' >&2; exit 2; }
tar czf "$STAGE/site.tar.gz" -C "$STAGE/site" .
REMOTE_STAGE=$(ssh "$SSH_HOST" 'mktemp -d -t ai-engineering.XXXXXXXX')
[[ "$REMOTE_STAGE" =~ ^/tmp/ai-engineering\.[a-zA-Z0-9]+$ ]] || exit 2
scp -q "$STAGE/site.tar.gz" "$SSH_HOST:$REMOTE_STAGE/site.tar.gz"
# Values below are constrained to shell-safe identifiers/paths above.
ssh "$SSH_HOST" "bash -s -- '$CTID' '$SITE_DIR' '$REMOTE_STAGE'" <<'REMOTE'
set -euo pipefail
ct=$1 site=$2 transfer=$3
release_id=$(basename "$transfer")
archive="/tmp/$release_id.tar.gz"
pct push "$ct" "$transfer/site.tar.gz" "$archive"
pct exec "$ct" -- bash -s -- "$site" "$release_id" "$archive" <<'CONTAINER'
set -euo pipefail
site=$1 id=$2 archive=$3
docroot="/var/www/sites/$site"
release="/var/www/releases/$site/$id"
vhost="/etc/nginx/sites-enabled/$site"
backup="/tmp/$id.vhost-backup"
legacy="/var/www/releases/$site/legacy-$id"
old_target=''
old_vhost=0
switched=0
legacy_moved=0
if [[ -L "$docroot" ]]; then old_target=$(readlink "$docroot"); fi
if [[ -e "$vhost" || -L "$vhost" ]]; then cp -a "$vhost" "$backup"; old_vhost=1; fi
rollback() {
  status=$?
  if [[ "$status" != 0 ]]; then
    if [[ "$switched" == 1 ]]; then rm -f "$docroot"; fi
    if [[ "$legacy_moved" == 1 ]]; then mv "$legacy" "$docroot";
    elif [[ "$switched" == 1 && -n "$old_target" ]]; then ln -s "$old_target" "$docroot"; fi
    rm -f "$vhost"
    if [[ "$old_vhost" == 1 ]]; then cp -a "$backup" "$vhost"; fi
    nginx -t && systemctl reload nginx || true
    echo 'Deployment failed; previous docroot/vhost restored.' >&2
  fi
  rm -f "$archive" "$backup" "$docroot.next-$id"
  exit "$status"
}
trap rollback EXIT
mkdir -p "$release" "$(dirname "$docroot")"
tar xzf "$archive" -C "$release"
find "$release" -type d -exec chmod 755 {} +
find "$release" -type f -exec chmod 644 {} +
# Write to a new regular file so an old vhost symlink target is never modified.
rm -f "$vhost"
printf 'server {\n listen 80;\n server_name %s;\n root %s;\n index index.html;\n location / { try_files $uri $uri/ =404; }\n}\n' "$site" "$docroot" > "$vhost"
nginx -t
ln -s "$release" "$docroot.next-$id"
if [[ -d "$docroot" && ! -L "$docroot" ]]; then mv "$docroot" "$legacy"; legacy_moved=1; fi
mv -Tf "$docroot.next-$id" "$docroot"
switched=1
systemctl reload nginx
for path in index.html reader.html reader-links.js files.json vendor/marked.min.js labs.zip books/01-map-and-llm-basics/book.md; do
  code=$(curl --fail --silent --show-error --max-time 15 --output /dev/null --write-out '%{http_code}' "http://127.0.0.1/$path" -H "Host: $site")
  [[ "$code" == 200 ]] || { echo "$path: expected 200, got $code" >&2; exit 1; }
  echo "$path: $code"
done
CONTAINER
REMOTE
# Public HTTPS is a distinct check: a LAN success is not a certificate/NPM success.
curl --fail --silent --show-error --max-time 20 --output /dev/null "https://$SITE_DIR/files.json"
echo "Published https://$SITE_DIR (CT $CTID). Previous release retained for rollback."
