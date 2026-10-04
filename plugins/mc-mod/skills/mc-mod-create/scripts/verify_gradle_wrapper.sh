#!/usr/bin/env bash
# =============================================================================
# verify_gradle_wrapper.sh [プロジェクトのパス]
#
# 雛形からコピーした Gradle Wrapper を、初めて ./gradlew を実行する前に検証する。
#   1. gradle/wrapper/gradle-wrapper.jar の SHA-256 を、Gradle 公式
#      （services.gradle.org）が公開しているチェックサムと照合
#   2. gradle-wrapper.properties の distributionUrl が公式 HTTPS URL か確認
#   3. distributionSha256Sum が未設定なら公式値を追記（以後 Gradle 本体の
#      ダウンロードも自動で検証される）
# 一致しなければ何も変更せず終了コード 1。
# =============================================================================
set -euo pipefail
dir="${1:-.}"
props="$dir/gradle/wrapper/gradle-wrapper.properties"
jar="$dir/gradle/wrapper/gradle-wrapper.jar"
die() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }
log() { printf '\033[1;34m[wrapper]\033[0m %s\n' "$*"; }

[[ -f "$props" && -f "$jar" ]] || die "Gradle Wrapper が見つかりません: $dir"
command -v curl >/dev/null || die "curl が必要です"

sha256() {
  if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1
  else shasum -a 256 "$1" | cut -d' ' -f1; fi
}
fetch() { curl -fsSL --proto '=https' --tlsv1.2 "$1"; }

url="$(sed -n 's/^distributionUrl=//p' "$props" | tr -d '\r' | sed 's#\\:#:#g')"
[[ "$url" =~ ^https://services\.gradle\.org/distributions/gradle-([0-9][0-9.]*(-rc-[0-9]+)?)-(bin|all)\.zip$ ]] \
  || die "distributionUrl が Gradle 公式の HTTPS URL ではありません: $url"
ver="${BASH_REMATCH[1]}"
log "Gradle $ver"

want_jar="$(fetch "https://services.gradle.org/distributions/gradle-${ver}-wrapper.jar.sha256" | tr -d '[:space:]')"
got_jar="$(sha256 "$jar")"
[[ "$want_jar" =~ ^[0-9a-f]{64}$ ]] || die "公式チェックサムを取得できませんでした"
[[ "$got_jar" == "$want_jar" ]] || die "gradle-wrapper.jar が公式のものと一致しません（実行しないでください）"
log "gradle-wrapper.jar: 公式と一致"

if grep -q '^distributionSha256Sum=' "$props"; then
  log "distributionSha256Sum は設定済み"
else
  want_dist="$(fetch "${url}.sha256" | tr -d '[:space:]')"
  [[ "$want_dist" =~ ^[0-9a-f]{64}$ ]] || die "配布物のチェックサムを取得できませんでした"
  printf 'distributionSha256Sum=%s\n' "$want_dist" >> "$props"
  log "distributionSha256Sum を追記しました"
fi
log "検証完了。./gradlew を実行して構いません"
