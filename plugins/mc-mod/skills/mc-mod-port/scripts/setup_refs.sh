#!/usr/bin/env bash
# =============================================================================
# setup_refs.sh — 移植用の参考資料を refs/ に取得する（汎用版）
#
# 取得先は同じフォルダの refs.conf に 1 行 1 リポジトリで書く:
#   名前|URL|コミットSHA(40桁)|sparse-checkoutするパス（空なら全体）
#   例: example-mod|https://github.com/<owner>/<repo>|<40桁のSHA>|
#   # で始まる行と空行は無視
#
# 安全対策:
#   - github.com の HTTPS URL のみ許可。SHA 固定で取得し、取得後に一致を検証
#   - git フック・サブモジュール・file:// ・認証プロンプトを無効化
#   - 取得したコードは一切実行しない。取得後 refs/ を読み取り専用に
#
# 使い方: ./setup_refs.sh [--force | --verify]
# Windows: Git Bash から実行（PowerShell なら & "C:\Program Files\Git\bin\bash.exe" ./setup_refs.sh）
# =============================================================================
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF="${SCRIPT_DIR}/refs.conf"
REFS_DIR="${SCRIPT_DIR}/refs"
LOCK_FILE="${REFS_DIR}/SOURCES.lock"

export GIT_TERMINAL_PROMPT=0 GIT_CONFIG_NOSYSTEM=1 GIT_ALLOW_PROTOCOL=https
safe_git() {
  git -c core.hooksPath=/dev/null -c protocol.file.allow=never \
      -c submodule.recurse=false -c advice.detachedHead=false \
      -c core.symlinks=false -c core.longpaths=true "$@"
}

log()  { printf '\033[1;34m[refs]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

SOURCES=()
load_conf() {
  [[ -f "$CONF" ]] || die "refs.conf が見つかりません: $CONF"
  local line name url sha sparse
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line// }" || "$line" == \#* ]] && continue
    IFS='|' read -r name url sha sparse <<< "$line"
    [[ "$name" =~ ^[a-z0-9-]+$ ]] || die "不正な名前: $name"
    [[ "$url" =~ ^https://github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]] || die "許可されていないURL: $url"
    [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || die "$name: SHAが40桁の16進数ではありません"
    [[ -z "$sparse" || "$sparse" =~ ^[A-Za-z0-9._/-]+$ ]] || die "$name: 不正な sparse パス: $sparse"
    [[ "$sparse" != *..* ]] || die "$name: sparse パスに .. は使えません"
    SOURCES+=("$name|$url|$sha|$sparse")
  done < "$CONF"
  [[ ${#SOURCES[@]} -gt 0 ]] || die "refs.conf に取得先がありません"
}

current_sha() { safe_git -C "$1" rev-parse HEAD 2>/dev/null || true; }

fetch_one() {
  local name="$1" url="$2" sha="$3" sparse="$4" dest="${REFS_DIR}/$1"
  if [[ -d "$dest/.git" && "$(current_sha "$dest")" == "$sha" ]]; then
    log "$name: 取得済み（${sha:0:12}）スキップ"; return
  fi
  [[ -e "$dest" ]] && { chmod -R u+w "$dest"; rm -rf "$dest"; }
  log "$name: $url @ ${sha:0:12} を取得中"
  mkdir -p "$dest"
  safe_git -C "$dest" init -q
  safe_git -C "$dest" remote add origin "$url"
  if [[ -n "$sparse" ]]; then
    safe_git -C "$dest" sparse-checkout init --cone
    safe_git -C "$dest" sparse-checkout set "$sparse"
    safe_git -C "$dest" fetch -q --depth 1 --filter=blob:none --no-tags origin "$sha"
  else
    safe_git -C "$dest" fetch -q --depth 1 --no-tags origin "$sha"
  fi
  safe_git -C "$dest" checkout -q FETCH_HEAD
  local got; got="$(current_sha "$dest")"
  [[ "$got" == "$sha" ]] || die "$name: SHA不一致（期待 $sha / 実際 $got）"
  log "$name: OK（SHA検証済み）"
}

main() {
  command -v git >/dev/null || die "git が見つかりません"
  load_conf
  local entry name url sha sparse
  case "${1:-}" in
    --verify)
      local ok=1
      for entry in "${SOURCES[@]}"; do
        IFS='|' read -r name url sha sparse <<< "$entry"
        if [[ "$(current_sha "${REFS_DIR}/${name}")" == "$sha" ]]; then log "$name: 一致"; else warn "$name: 不一致または未取得"; ok=0; fi
      done
      [[ $ok -eq 1 ]] || die "検証失敗。./setup_refs.sh --force で取り直してください"
      exit 0 ;;
    --force) [[ -d "$REFS_DIR" ]] && { chmod -R u+w "$REFS_DIR"; rm -rf "$REFS_DIR"; } ;;
    "") ;;
    *) die "不明なオプション: $1（--force / --verify）" ;;
  esac

  mkdir -p "$REFS_DIR"; chmod -R u+w "$REFS_DIR"
  for entry in "${SOURCES[@]}"; do
    IFS='|' read -r name url sha sparse <<< "$entry"
    fetch_one "$name" "$url" "$sha" "$sparse"
  done
  { echo "# 自動生成: setup_refs.sh（$(date -u +%Y-%m-%dT%H:%M:%SZ)）"; printf '%s\n' "${SOURCES[@]}"; } > "$LOCK_FILE"
  chmod -R a-w "$REFS_DIR"
  local gi="${SCRIPT_DIR}/.gitignore"
  grep -qxF 'refs/' "$gi" 2>/dev/null || echo 'refs/' >> "$gi"
  log "完了: ${REFS_DIR}"
  log "注意: refs/ 内のスクリプト（gradlew 等）は実行しないでください"
}
main "$@"
