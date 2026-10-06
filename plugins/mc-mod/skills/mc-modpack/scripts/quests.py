#!/usr/bin/env python3
"""
quests.py — FTB Quests（Minecraft 1.21 系・SNBT 形式）のクエスト作成を補助する

  newid [個数] [--pack <パック>]
      既存のクエストファイルと重ならない 16 桁の大文字 16 進 ID を生成
  items <パック> [--refresh]
      アイテム ID の一覧を作る（<パック>/run/cache/items.txt）
        バニラ: Mojang 公式のサーバー jar を SHA-1 照合して取得し、データ生成の registries レポートから
        MOD  : run/server/mods/*.jar 内の assets/<ns>/lang/en_us.json の item./block. キーから（近似）
      ※ 先に boot_test.py で run/server/mods を用意しておくこと。side=client の MOD のアイテムは含まれない
  find <パック> <語> [<語> ...]
      アイテム一覧から部分一致で検索（クエストに使う ID を探すとき）
  validate <パック>
      config/ftbquests/quests/ を検査: ID の形式・重複、filename とファイル名の一致、
      依存先の実在、依存の循環、アイテム ID の実在（items の一覧が必要）、タイトルの翻訳漏れ

Python 3.11 以上。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
import zipfile
from pathlib import Path

HEX16 = re.compile(r'"?\b([0-9A-F]{16})\b"?')
ID_FIELD = re.compile(r'(?<![\w.])id:\s*"?([0-9A-F]{16})"?(?![0-9A-Za-z])')
ITEM_ID = re.compile(r'\bid:\s*"([a-z0-9_.\-]+:[a-z0-9_./\-]+)"')
MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
UA = {"User-Agent": "nokopi-skills/mc-modpack quests"}


def quests_dir(pack: Path) -> Path:
    return pack / "config" / "ftbquests" / "quests"


def all_snbt(pack: Path):
    d = quests_dir(pack)
    return [p for p in d.rglob("*.snbt") if "lang" not in p.relative_to(d).parts] if d.exists() else []


def existing_ids(pack: Path | None) -> set[str]:
    ids = set()
    if pack:
        for p in all_snbt(pack):
            ids |= set(ID_FIELD.findall(p.read_text(encoding="utf-8", errors="replace")))
    return ids


def cmd_newid(a):
    used = existing_ids(Path(a.pack) if a.pack else None)
    out = []
    while len(out) < a.count:
        i = secrets.token_hex(8).upper()
        if i not in used and i not in out and not i.startswith("0000"):
            out.append(i)
    print("\n".join(out))


def fetch(url):
    if not url.startswith("https://"):
        sys.exit(f"HTTPS 以外は使いません: {url}")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def vanilla_items(mc: str, cache: Path) -> set[str]:
    out = cache / f"vanilla-{mc}.txt"
    if out.exists():
        return set(out.read_text(encoding="utf-8").split())
    manifest = json.loads(fetch(MANIFEST))
    entry = next((v for v in manifest["versions"] if v["id"] == mc), None)
    if not entry:
        sys.exit(f"Mojang のバージョン一覧に {mc} がありません")
    vjson = fetch(entry["url"])
    if hashlib.sha1(vjson).hexdigest() != entry["sha1"]:
        sys.exit("バージョン情報の SHA-1 が一致しません")
    srv = json.loads(vjson)["downloads"]["server"]
    jar = fetch(srv["url"])
    if hashlib.sha1(jar).hexdigest() != srv["sha1"]:
        sys.exit("サーバー jar の SHA-1 が一致しません")
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "server.jar").write_bytes(jar)
        print("バニラのレジストリを書き出し中（Java が必要）…", file=sys.stderr)
        subprocess.run(["java", "-DbundlerMainClass=net.minecraft.data.Main", "-jar", "server.jar",
                        "--reports", "--output", "gen"], cwd=td, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        reg = json.loads((Path(td) / "gen" / "reports" / "registries.json").read_text(encoding="utf-8"))
    items = set(reg["minecraft:item"]["entries"].keys())
    out.write_text("\n".join(sorted(items)) + "\n", encoding="utf-8")
    return items


def mod_items(mods_dir: Path) -> dict[str, set[str]]:
    found = {}
    for jar in sorted(mods_dir.glob("*.jar")):
        try:
            with zipfile.ZipFile(jar) as z:
                for name in z.namelist():
                    m = re.fullmatch(r"assets/([a-z0-9_.\-]+)/lang/en_us\.json", name)
                    if not m:
                        continue
                    ns = m.group(1)
                    try:
                        data = json.loads(z.read(name).decode("utf-8", errors="replace"))
                    except json.JSONDecodeError:
                        continue
                    for k in data:
                        km = re.fullmatch(rf"(?:item|block)\.{re.escape(ns)}\.([a-z0-9_./\-]+)", k)
                        if km and "." not in km.group(1):
                            found.setdefault(jar.name, set()).add(f"{ns}:{km.group(1)}")
        except zipfile.BadZipFile:
            continue
    return found


def cmd_items(a):
    pack = Path(a.pack)
    mc = tomllib.loads((pack / "pack.toml").read_text(encoding="utf-8"))["versions"]["minecraft"]
    cache = pack / "run" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    if a.refresh:
        (cache / f"vanilla-{mc}.txt").unlink(missing_ok=True)
    items = set(vanilla_items(mc, cache))
    mods_dir = pack / "run" / "server" / "mods"
    if not mods_dir.exists():
        print("注意: run/server/mods がありません。先に boot_test.py を実行してください（今はバニラのみ）", file=sys.stderr)
    else:
        per_jar = mod_items(mods_dir)
        for s in per_jar.values():
            items |= s
        print(f"MOD {len(per_jar)} 個からアイテム候補を抽出", file=sys.stderr)
    (cache / "items.txt").write_text("\n".join(sorted(items)) + "\n", encoding="utf-8")
    print(f"{len(items)} 件 → {cache / 'items.txt'}")


def load_items(pack: Path) -> set[str] | None:
    p = pack / "run" / "cache" / "items.txt"
    return set(p.read_text(encoding="utf-8").split()) if p.exists() else None


def cmd_find(a):
    items = load_items(Path(a.pack))
    if items is None:
        sys.exit("先に `quests.py items <パック>` を実行してください")
    words = [w.lower() for w in a.words]
    for i in sorted(items):
        if all(w in i for w in words):
            print(i)


def block_of(text: str, key: str):
    """key: [ ... ] の中身を返す（入れ子の [] を考慮）"""
    out = []
    for m in re.finditer(rf"\b{key}:\s*\[", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"[": 1, "]": -1}.get(text[i], 0)
            i += 1
        out.append(text[m.end():i - 1])
    return out


def split_quests(chapter_text: str):
    """quests: [ {..} {..} ] を各クエストの文字列に分ける"""
    blocks = block_of(chapter_text, "quests")
    if not blocks:
        return []
    body, quests, depth, start = blocks[0], [], 0, None
    for i, ch in enumerate(body):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                quests.append(body[start:i + 1])
    return quests


def top_level_id(obj: str):
    m = re.search(r'^\{\s*(?:[^{}\[\]]*?\n)?\s*id:\s*"?([0-9A-F]{16})"?', obj, re.S)
    if m:
        return m.group(1)
    depth = 0
    for line in obj.splitlines():
        if depth == 1:
            mm = re.match(r'\s*id:\s*"?([0-9A-F]{16})"?\s*$', line)
            if mm:
                return mm.group(1)
        depth += line.count("{") + line.count("[") - line.count("}") - line.count("]")
    return None


def cmd_validate(a):
    pack = Path(a.pack)
    d = quests_dir(pack)
    if not d.exists():
        sys.exit(f"クエストフォルダがありません: {d}")
    errors, warns = [], []
    id_where: dict[str, list[str]] = {}
    quest_deps: dict[str, list[str]] = {}
    chapters, quests = [], []
    item_refs = []

    for p in all_snbt(pack):
        rel = p.relative_to(d).as_posix()
        t = p.read_text(encoding="utf-8", errors="replace")
        if t.count("{") != t.count("}") or t.count("[") != t.count("]"):
            errors.append(f"{rel}: 括弧の数が合っていません")
        for i in ID_FIELD.findall(t):
            id_where.setdefault(i, []).append(rel)
        for bad in re.findall(r'(?<![\w.])id:\s*"?([0-9A-Za-z]{16})"?(?![0-9A-Za-z:])', t):
            if not re.fullmatch(r"[0-9A-F]{16}", bad):
                errors.append(f"{rel}: ID の形式が不正（大文字 16 進 16 桁）: {bad}")
        item_refs += [(rel, m) for m in ITEM_ID.findall(t)]
        if p.parent.name == "chapters":
            fm = re.search(r'^\s*filename:\s*"([^"]+)"', t, re.M)
            if not fm:
                errors.append(f"{rel}: filename がありません")
            elif fm.group(1) != p.stem:
                errors.append(f"{rel}: filename \"{fm.group(1)}\" がファイル名と一致しません")
            cid = top_level_id(t.strip())
            if cid:
                chapters.append(cid)
            for q in split_quests(t):
                qid = top_level_id(q)
                if not qid:
                    errors.append(f"{rel}: id のないクエストがあります")
                    continue
                quests.append(qid)
                deps = []
                for b in block_of(q, "dependencies"):
                    deps += HEX16.findall(b)
                quest_deps[qid] = deps

    for i, where in id_where.items():
        if len(where) > 1:
            errors.append(f"ID {i} が重複: {', '.join(where)}")
    for q, deps in quest_deps.items():
        for dep in deps:
            if dep not in id_where:
                errors.append(f"クエスト {q} の依存先 {dep} が存在しません")
    # 循環検出
    state = {}
    def visit(n, path):
        if state.get(n) == 1:
            errors.append("依存が循環しています: " + " → ".join(path + [n]))
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in quest_deps.get(n, []):
            if m in quest_deps:
                visit(m, path + [n])
        state[n] = 2
    for q in quest_deps:
        visit(q, [])

    items = load_items(pack)
    if items is None:
        warns.append("アイテム一覧がないため、アイテム ID は未検査（quests.py items を実行）")
    else:
        for rel, iid in item_refs:
            if iid.startswith("ftbquests:"):
                continue
            if iid not in items:
                warns.append(f"{rel}: アイテム {iid} が一覧にありません（存在しない ID か、side=client の MOD のもの）")

    langs = sorted((d / "lang").glob("*.snbt")) if (d / "lang").exists() else []
    if not langs:
        warns.append("lang/ に翻訳ファイルがありません")
    for lp in langs:
        lt = lp.read_text(encoding="utf-8", errors="replace")
        for c in chapters:
            if f"chapter.{c}.title" not in lt:
                warns.append(f"{lp.name}: チャプター {c} のタイトルがありません")
        missing = [q for q in quests if f"quest.{q}.title" not in lt]
        if missing:
            warns.append(f"{lp.name}: タイトル未設定のクエスト {len(missing)} 件（最初のタスクの名前で表示される）: "
                         + ", ".join(missing[:5]) + (" …" if len(missing) > 5 else ""))

    print(f"チャプター {len(chapters)} / クエスト {len(quests)} / ID {len(id_where)}")
    for e in errors:
        print(f"✘ {e}")
    for w in warns:
        print(f"△ {w}")
    if not errors and not warns:
        print("問題は見つかりませんでした")
    sys.exit(1 if errors else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("newid"); n.add_argument("count", type=int, nargs="?", default=1); n.add_argument("--pack")
    i = sub.add_parser("items"); i.add_argument("pack"); i.add_argument("--refresh", action="store_true")
    f = sub.add_parser("find"); f.add_argument("pack"); f.add_argument("words", nargs="+")
    v = sub.add_parser("validate"); v.add_argument("pack")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    {"newid": cmd_newid, "items": cmd_items, "find": cmd_find, "validate": cmd_validate}[a.cmd](a)


if __name__ == "__main__":
    main()
