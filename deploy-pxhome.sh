#!/usr/bin/env bash
# Зеркало devops-ридера на pxhome, LXC 109 ("alexa"): devops.adelfos.ru.
# Контейнер: IP 192.168.0.109, nginx :80, docroot /var/www/sites/devops.adelfos.ru.
# Внешний доступ: devops.adelfos.ru через Nginx Proxy Manager (LXC 101) → 192.168.0.109:80.
# Домен и NPM proxy host — вручную, разово (как для bass2).
#
# jino НЕ трогается: adelfos.ru/devops продолжает работать (это зеркало, не переезд).
#
# Требуется ssh-алиас "pxhome" (Tailscale, работает откуда угодно) — см. ~/.ssh/config.
#
# Раскладка на сервере повторяет jino: index.html/reader.html/files.json в корне docroot,
# папки книг NN-* — в подкаталоге books/. reader.html сначала грузит books/<книга>/<файл>.
set -euo pipefail

CTID="${CTID:-109}"
SSH_HOST="${SSH_HOST:-pxhome}"
SITE_DIR="${SITE_DIR:-ai-engineering.adelfos.ru}"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT_DIR/docs/books"
STAGE="$(mktemp -d)"
TAR="/tmp/devops-site.tar.gz"
VHOST="/tmp/devops-vhost.conf"

echo "→ Собираю staging (движок в корень + книги в books/) …"
mkdir -p "$STAGE/books"
cp "$SRC/index.html" "$SRC/reader.html" "$SRC/files.json" "$STAGE/"
shopt -s nullglob
for d in "$SRC"/[0-9][0-9]-*/ ; do cp -r "$d" "$STAGE/books/"; done
shopt -u nullglob
echo "  книг в books/: $(find "$STAGE/books" -maxdepth 1 -mindepth 1 -type d | wc -l)"

echo "→ Упаковываю …"
tar czf "$TAR" -C "$STAGE" .
rm -rf "$STAGE"

echo "→ Готовлю vhost (fallback =404, не /index.html — ридер полагается на 404) …"
cat > "$VHOST" <<EOF
server {
    listen 80;
    server_name $SITE_DIR;
    root /var/www/sites/$SITE_DIR;
    index index.html;
    location / { try_files \$uri \$uri/ =404; }
}
EOF

echo "→ Копирую на $SSH_HOST …"
scp -q "$TAR" "$SSH_HOST:/tmp/devops-site.tar.gz"
scp -q "$VHOST" "$SSH_HOST:/tmp/devops-vhost.conf"
rm -f "$TAR" "$VHOST"

echo "→ Разворачиваю в LXC $CTID …"
ssh "$SSH_HOST" "
  set -e
  pct push $CTID /tmp/devops-vhost.conf /etc/nginx/sites-enabled/$SITE_DIR
  pct push $CTID /tmp/devops-site.tar.gz /tmp/devops-site.tar.gz
  pct exec $CTID -- rm -rf /var/www/sites/$SITE_DIR
  pct exec $CTID -- mkdir -p /var/www/sites/$SITE_DIR
  pct exec $CTID -- tar xzf /tmp/devops-site.tar.gz -C /var/www/sites/$SITE_DIR
  pct exec $CTID -- rm /tmp/devops-site.tar.gz
  # tar переносит режим записи '.' (mktemp -d = 700) на docroot → nginx (www-data) не войдёт. Возвращаем 755.
  pct exec $CTID -- chmod 755 /var/www/sites/$SITE_DIR
  pct exec $CTID -- nginx -t
  pct exec $CTID -- systemctl reload nginx
  echo '--- self-check (Host: $SITE_DIR) ---'
  pct exec $CTID -- curl -s -o /dev/null -w 'index.html:   %{http_code}\n' http://127.0.0.1/index.html  -H 'Host: $SITE_DIR'
  pct exec $CTID -- curl -s -o /dev/null -w 'reader.html:  %{http_code}\n' http://127.0.0.1/reader.html -H 'Host: $SITE_DIR'
  pct exec $CTID -- curl -s -o /dev/null -w 'files.json:   %{http_code}\n' http://127.0.0.1/files.json  -H 'Host: $SITE_DIR'
  pct exec $CTID -- curl -s -o /dev/null -w 'book chapter: %{http_code}\n' http://127.0.0.1/books/01-linux-for-devops/book.md -H 'Host: $SITE_DIR'
  rm /tmp/devops-vhost.conf
"
echo "✓ Готово на CT $CTID (docroot /var/www/sites/$SITE_DIR)."
echo "  Разово вручную: DNS $SITE_DIR + NPM proxy host → 192.168.0.109:80 + SSL. Затем: https://$SITE_DIR"
