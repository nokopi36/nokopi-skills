#!/usr/bin/env python3
"""
modrinth.py — Modrinth API でモッドパック用の MOD を調べる（読み取り専用、標準ライブラリのみ）

  search <キーワード> --mc 1.21.1 --loader neoforge [--limit 10]
      対応バージョン・ローダーで絞って検索
  info <slug> [<slug> ...] --mc 1.21.1 --loader neoforge
      動作側（クライアント/サーバー）、ライセンス、ソース、対応する最新版、必須依存、非互換を表示
  check <packwiz のパックフォルダ>
      パック内の Modrinth 由来 MOD について、必須依存の不足・非互換の同居・side 設定の食い違いを検出
      （CurseForge 由来の MOD は対象外として一覧だけ出す）

Python 3.11 以上（tomllib を使う）。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import tomllib
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.modrinth.com/v2"
UA = "nokopi-skills/mc-modpack (Claude Code skill; https://github.com/nokopi36/nokopi-skills)"


def get(path: str, **params) -> object:
    q = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in params.items() if v is not None}
    url = f"{API}{path}" + (f"?{urllib.parse.urlencode(q)}" if q else "")
    for attempt in range(3):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(int(e.headers.get("X-Ratelimit-Reset", "5")))
                continue
            if e.code == 404:
                return None
            raise
    raise RuntimeError("Modrinth API のレート制限に達しました")


def chunks(xs, n=100):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def projects_by_ids(ids):
    out = {}
    for c in chunks(list(ids)):
        for p in get("/projects", ids=c) or []:
            out[p["id"]] = p
    return out


def side_label(p):
    return f"client={p.get('client_side')} server={p.get('server_side')}"


def cmd_search(a):
    facets = [["project_type:mod"], [f"versions:{a.mc}"], [f"categories:{a.loader}"]]
    res = get("/search", query=a.query, facets=facets, limit=a.limit, index="relevance")
    for h in res["hits"]:
        print(f"{h['slug']:<32} {h['downloads']:>10,} DL  {h['title']} — {h['description'][:70]}")
        print(f"{'':<32} client={h.get('client_side')} server={h.get('server_side')} license={h.get('license')}")


def compatible_version(slug_or_id, mc, loader):
    vs = get(f"/project/{slug_or_id}/version", loaders=[loader], game_versions=[mc]) or []
    vs.sort(key=lambda v: v["date_published"], reverse=True)
    release = [v for v in vs if v["version_type"] == "release"]
    return (release or vs or [None])[0]


def cmd_info(a):
    for slug in a.slugs:
        p = get(f"/project/{slug}")
        if not p:
            print(f"■ {slug}: 見つかりません\n")
            continue
        print(f"■ {p['title']} ({p['slug']})")
        print(f"  {side_label(p)}  license={p['license']['id']}  source={p.get('source_url') or 'なし'}")
        v = compatible_version(p["id"], a.mc, a.loader)
        if not v:
            print(f"  {a.mc} / {a.loader} の対応版なし\n")
            continue
        print(f"  対応版: {v['version_number']} ({v['version_type']}, {v['date_published'][:10]})")
        deps = v.get("dependencies") or []
        names = projects_by_ids({d["project_id"] for d in deps if d.get("project_id")})
        for kind, label in (("required", "必須依存"), ("optional", "任意依存"), ("incompatible", "非互換")):
            xs = [names.get(d.get("project_id"), {}).get("slug", d.get("project_id") or d.get("file_name"))
                  for d in deps if d["dependency_type"] == kind]
            if xs:
                print(f"  {label}: {', '.join(xs)}")
        print()


def load_pack(pack_dir: Path):
    pack = tomllib.loads((pack_dir / "pack.toml").read_text(encoding="utf-8"))
    index_path = pack_dir / pack["index"]["file"]
    index = tomllib.loads(index_path.read_text(encoding="utf-8"))
    mods = []
    for f in index.get("files", []):
        if not f.get("metafile"):
            continue
        meta = tomllib.loads((index_path.parent / f["file"]).read_text(encoding="utf-8"))
        mods.append({"file": f["file"], **meta})
    return pack, mods


def cmd_check(a):
    pack_dir = Path(a.pack)
    pack, mods = load_pack(pack_dir)
    mr = {m["update"]["modrinth"]["mod-id"]: m for m in mods if "modrinth" in m.get("update", {})}
    others = [m["name"] for m in mods if "modrinth" not in m.get("update", {})]
    print(f"パック: {pack.get('name')}  Minecraft {pack['versions'].get('minecraft')}  "
          f"MOD {len(mods)} 件（Modrinth {len(mr)} / その他 {len(others)}）\n")

    versions = {}
    for c in chunks([m["update"]["modrinth"]["version"] for m in mr.values()]):
        for v in get("/versions", ids=c) or []:
            versions[v["project_id"]] = v
    projects = projects_by_ids(mr.keys())

    missing, incompatible, side_issues = {}, [], []
    for pid, m in mr.items():
        v = versions.get(pid)
        if not v:
            continue
        for d in v.get("dependencies") or []:
            dp = d.get("project_id")
            if d["dependency_type"] == "required" and dp and dp not in mr:
                missing.setdefault(dp, []).append(m["name"])
            if d["dependency_type"] == "incompatible" and dp in mr:
                incompatible.append((m["name"], mr[dp]["name"]))
        p = projects.get(pid, {})
        side = m.get("side", "both")
        if p.get("server_side") == "unsupported" and side != "client":
            side_issues.append(f"{m['name']}: サーバー非対応なのに side={side}（client にすべき）")
        if p.get("client_side") == "unsupported" and side != "server":
            side_issues.append(f"{m['name']}: クライアント非対応なのに side={side}（server にすべき）")

    if missing:
        names = projects_by_ids(missing.keys())
        print("● 不足している必須依存")
        for dp, by in missing.items():
            print(f"  {names.get(dp, {}).get('slug', dp)}  ← {', '.join(by)}")
    if incompatible:
        print("● 非互換と宣言されている組み合わせ")
        for x, y in incompatible:
            print(f"  {x} ✕ {y}")
    if side_issues:
        print("● side 設定")
        for s in side_issues:
            print(f"  {s}")
    if others:
        print(f"● Modrinth 以外の MOD（依存は未確認）: {', '.join(others)}")
    if not (missing or incompatible or side_issues):
        print("問題は見つかりませんでした（Modrinth で宣言されている情報の範囲で）")
    return 1 if (missing or incompatible) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--mc", required=True)
    s.add_argument("--loader", required=True); s.add_argument("--limit", type=int, default=10)
    i = sub.add_parser("info"); i.add_argument("slugs", nargs="+"); i.add_argument("--mc", required=True)
    i.add_argument("--loader", required=True)
    c = sub.add_parser("check"); c.add_argument("pack")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit({"search": cmd_search, "info": cmd_info, "check": cmd_check}[a.cmd](a) or 0)


if __name__ == "__main__":
    main()
