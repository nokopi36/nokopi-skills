#!/usr/bin/env bash
# 新しいプラグインの雛形を作り、marketplace.json に登録する。
# 使い方: tools/new_plugin.sh <プラグイン名> "<説明>" [最初のスキル名]
#   プラグイン名・スキル名は小文字英数字とハイフン（例: android, git-helper）
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
name="${1:?使い方: tools/new_plugin.sh <プラグイン名> \"<説明>\" [最初のスキル名]}"
desc="${2:?説明を指定してください}"
skill="${3:-$name}"
re='^[a-z0-9]+(-[a-z0-9]+)*$'
[[ "$name" =~ $re && "$skill" =~ $re ]] || { echo "名前は小文字英数字とハイフンのみ" >&2; exit 1; }
dir="$ROOT/plugins/$name"
[[ ! -e "$dir" ]] || { echo "すでに存在します: plugins/$name" >&2; exit 1; }

owner="$(python3 -c "import json;print(json.load(open('$ROOT/.claude-plugin/marketplace.json'))['owner']['name'])")"
mkdir -p "$dir/.claude-plugin" "$dir/skills/$skill"
python3 - "$dir" "$name" "$desc" "$owner" "$skill" "$ROOT" <<'PY'
import json, sys
d, name, desc, owner, skill, root = sys.argv[1:]
json.dump({"name": name, "version": "0.1.0", "description": desc,
           "author": {"name": owner}, "license": "MIT"},
          open(f"{d}/.claude-plugin/plugin.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(f"{d}/skills/{skill}/SKILL.md", "w", encoding="utf-8").write(
f"""---
name: {skill}
description: TODO — このスキルが何をするか、どんなときに使うかを具体的に書く
---

# {skill}

TODO
""")
mp = f"{root}/.claude-plugin/marketplace.json"
m = json.load(open(mp, encoding="utf-8"))
m["plugins"].append({"name": name, "source": f"./plugins/{name}", "description": desc})
json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(mp, "a", encoding="utf-8").write("\n")
PY
printf '\n' >> "$dir/.claude-plugin/plugin.json"
echo "作成しました: plugins/$name（スキル: $skill）"
echo "次: SKILL.md を書く → README.md のプラグイン一覧に追記 → claude plugin validate ."
