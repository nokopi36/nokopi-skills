#!/usr/bin/env bash
# tools/shared.conf に従って、shared/ の共通ファイルを各スキルへコピーする。
# 使い方: tools/sync_shared.sh          コピーする
#         tools/sync_shared.sh --check  ずれがあれば一覧を出して終了コード 1（CI 用）
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF="$ROOT/tools/shared.conf"
mode="${1:-sync}"; drift=0; n=0
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%$'\r'}"
  [[ -z "${line// }" || "$line" == \#* ]] && continue
  IFS='|' read -r src dst <<< "$line"
  [[ "$src" == shared/* && "$dst" == plugins/* && "$src$dst" != *..* ]] || { echo "不正な行: $line" >&2; exit 1; }
  [[ -f "$ROOT/$src" ]] || { echo "原本がありません: $src" >&2; exit 1; }
  n=$((n+1))
  if [[ "$mode" == "--check" ]]; then
    cmp -s "$ROOT/$src" "$ROOT/$dst" || { echo "ずれ: $dst"; drift=1; }
  else
    mkdir -p "$(dirname "$ROOT/$dst")"; cp "$ROOT/$src" "$ROOT/$dst"
    [[ "$dst" == *.sh ]] && chmod +x "$ROOT/$dst"
  fi
done < "$CONF"
if [[ "$mode" == "--check" ]]; then
  if [[ $drift -eq 0 ]]; then echo "共通ファイル ${n} 件すべて一致"; else echo "tools/sync_shared.sh を実行してください" >&2; exit 1; fi
else
  echo "${n} 件を同期しました"
fi
