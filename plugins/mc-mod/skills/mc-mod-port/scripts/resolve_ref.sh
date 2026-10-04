#!/usr/bin/env bash
# resolve_ref.sh <github-url> [branch]
#   branch を指定するとそのブランチ先頭の SHA を、省略するとブランチ一覧を表示する。
#   git ls-remote を呼ぶだけで、何もダウンロード・実行しない。
set -euo pipefail
url="${1:?使い方: resolve_ref.sh <github-url> [branch]}"
[[ "$url" =~ ^https://github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]] || { echo "github.com の HTTPS URL のみ対応: $url" >&2; exit 1; }
export GIT_TERMINAL_PROMPT=0 GIT_ALLOW_PROTOCOL=https
if [[ -n "${2:-}" ]]; then
  sha="$(git ls-remote --heads "$url" "refs/heads/$2" | cut -f1)"
  [[ -n "$sha" ]] || { echo "ブランチが見つかりません: $2" >&2; exit 1; }
  echo "$sha"
else
  echo "# default: $(git ls-remote --symref "$url" HEAD | awk '/^ref:/{sub("refs/heads/","",$2); print $2}')"
  git ls-remote --heads "$url" | sed 's#refs/heads/##' | awk '{print $2"\t"$1}' | sort -V
fi
