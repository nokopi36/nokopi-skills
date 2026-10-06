#!/usr/bin/env python3
"""
boot_test.py — packwiz のパックを専用サーバーとして起動し、クラッシュしないか確かめる

  python boot_test.py <パックフォルダ> --accept-eula [--timeout 900] [--keep-world] [--memory 6G]

流れ:
  1. pack.toml から Minecraft とローダー（neoforge / fabric）のバージョンを読む
  2. <パック>/run/server/ にローダーのサーバーを用意（初回のみ）
       NeoForge: maven.neoforged.net のインストーラーをチェックサム照合してから --installServer
       Fabric  : meta.fabricmc.net の公式サーバーランチャー（HTTPS）
  3. `packwiz serve` でパックを配信し、packwiz-installer-bootstrap（SHA-256 固定）で
     サーバー側の MOD と設定を取得（side=client の MOD は入らない）
  4. サーバーを起動し、"Done (" が出たら stop を送る。クラッシュ・タイムアウトを判定
  5. 結果と、ログ内の ERROR／例外の要約、クラッシュレポートの場所を表示

--accept-eula: Minecraft EULA（https://aka.ms/MinecraftEULA）への同意。ユーザー本人が同意した場合のみ付ける。
必要なもの: Java（対象バージョンに合うもの）、packwiz（PATH 上か、--packwiz で指定）。Python 3.11 以上。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tomllib
import urllib.request
from pathlib import Path

BOOTSTRAP_URL = "https://github.com/packwiz/packwiz-installer-bootstrap/releases/download/v0.0.3/packwiz-installer-bootstrap.jar"
BOOTSTRAP_SHA256 = "a8fbb24dc604278e97f4688e82d3d91a318b98efc08d5dbfcbcbcab6443d116c"
NEOFORGE_MAVEN = "https://maven.neoforged.net/releases/net/neoforged/neoforge"
FABRIC_META = "https://meta.fabricmc.net/v2/versions"
SERVE_PORT = 8085
SERVER_PORT = 25599
UA = {"User-Agent": "nokopi-skills/mc-modpack boot_test"}


def log(msg):
    print(f"[boot] {msg}", flush=True)


def die(msg):
    print(f"[error] {msg}", file=sys.stderr, flush=True)
    sys.exit(2)


def fetch(url: str) -> bytes:
    if not url.startswith("https://"):
        die(f"HTTPS 以外は使いません: {url}")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def download(url: str, dest: Path, sha256: str | None = None, checksum_from_same_host: bool = False):
    data = fetch(url)
    if sha256:
        got = hashlib.sha256(data).hexdigest()
        if got != sha256:
            die(f"チェックサム不一致: {url}\n  期待 {sha256}\n  実際 {got}")
    elif checksum_from_same_host:
        for algo in ("sha512", "sha256", "sha1"):
            try:
                want = fetch(f"{url}.{algo}").decode().split()[0].strip().lower()
            except Exception:
                continue
            got = hashlib.new(algo, data).hexdigest()
            if got != want:
                die(f"{algo} 不一致: {url}")
            log(f"{dest.name}: {algo} 照合 OK")
            break
        else:
            die(f"チェックサムを取得できませんでした: {url}")
    dest.write_bytes(data)


def read_pack(pack_dir: Path):
    pack = tomllib.loads((pack_dir / "pack.toml").read_text(encoding="utf-8"))
    v = pack["versions"]
    mc = v["minecraft"]
    if "neoforge" in v:
        return mc, "neoforge", v["neoforge"]
    if "fabric" in v:
        return mc, "fabric", v["fabric"]
    die(f"未対応のローダーです（neoforge / fabric のみ）: {list(v)}")


def java_ok():
    if not shutil.which("java"):
        die("java が見つかりません")
    out = subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.splitlines()
    log(f"Java: {out[0] if out else '?'}")


def install_neoforge(server: Path, ver: str):
    if list(server.glob("libraries/net/neoforged/neoforge/*/unix_args.txt")):
        return
    inst = server / f"neoforge-{ver}-installer.jar"
    log(f"NeoForge {ver} のインストーラーを取得")
    download(f"{NEOFORGE_MAVEN}/{ver}/neoforge-{ver}-installer.jar", inst, checksum_from_same_host=True)
    log("NeoForge サーバーをインストール中（初回は数分かかります）")
    r = subprocess.run(["java", "-jar", inst.name, "--installServer"], cwd=server)
    if r.returncode != 0:
        die("NeoForge のインストールに失敗しました")
    inst.unlink(missing_ok=True)


def install_fabric(server: Path, mc: str, loader: str):
    jar = server / "fabric-server-launch.jar"
    if jar.exists():
        return
    installers = json.loads(fetch(f"{FABRIC_META}/installer"))
    inst = next(i["version"] for i in installers if i.get("stable"))
    log(f"Fabric サーバーランチャー（loader {loader} / installer {inst}）を取得")
    download(f"{FABRIC_META}/loader/{mc}/{loader}/{inst}/server/jar", jar)


def server_command(server: Path, loader: str, memory: str):
    if loader == "neoforge":
        name = "win_args.txt" if os.name == "nt" else "unix_args.txt"
        args = sorted(server.glob(f"libraries/net/neoforged/neoforge/*/{name}"))
        if not args:
            die("NeoForge の起動引数ファイルが見つかりません")
        return ["java", f"-Xmx{memory}", f"@{args[-1].relative_to(server).as_posix()}", "nogui"]
    return ["java", f"-Xmx{memory}", "-jar", "fabric-server-launch.jar", "nogui"]


def sync_mods(pack_dir: Path, server: Path, packwiz: str):
    boot = server / "packwiz-installer-bootstrap.jar"
    if not boot.exists():
        download(BOOTSTRAP_URL, boot, sha256=BOOTSTRAP_SHA256)
    subprocess.run([packwiz, "refresh"], cwd=pack_dir, check=True)
    serve = subprocess.Popen([packwiz, "serve", "--port", str(SERVE_PORT)], cwd=pack_dir,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(2)
        log("サーバー側の MOD と設定を取得中")
        r = subprocess.run(["java", "-jar", boot.name, "-g", "-s", "server",
                            f"http://localhost:{SERVE_PORT}/pack.toml"], cwd=server)
        if r.returncode != 0:
            die("packwiz-installer が失敗しました（CurseForge の配布禁止 MOD などは手動配置が必要な場合があります）")
    finally:
        serve.terminate()


def prepare_world(server: Path, keep_world: bool):
    (server / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    props = server / "server.properties"
    lines = props.read_text(encoding="utf-8").splitlines() if props.exists() else []
    conf = {l.split("=", 1)[0]: l for l in lines if "=" in l and not l.startswith("#")}
    conf["server-port"] = f"server-port={SERVER_PORT}"
    conf["online-mode"] = "online-mode=false"
    conf["server-ip"] = "server-ip=127.0.0.1"  # テスト中は外部から接続できないように
    conf.setdefault("level-name", "level-name=boot_test_world")
    props.write_text("\n".join(conf.values()) + "\n", encoding="utf-8")
    if not keep_world:
        shutil.rmtree(server / "boot_test_world", ignore_errors=True)
    for p in (server / "crash-reports").glob("*.txt") if (server / "crash-reports").exists() else []:
        p.rename(p.with_suffix(".old"))


def run_server(server: Path, cmd, timeout: int):
    log(f"起動: {' '.join(cmd)}（タイムアウト {timeout} 秒）")
    start = time.time()
    proc = subprocess.Popen(cmd, cwd=server, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    state = {"done": None}

    def reader():
        for line in proc.stdout:
            if state["done"] is None and re.search(r"Done \([\d.]+s\)!", line):
                state["done"] = time.time() - start
                try:
                    proc.stdin.write("stop\n"); proc.stdin.flush()
                except Exception:
                    pass
    threading.Thread(target=reader, daemon=True).start()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        return "timeout", None, time.time() - start
    if state["done"] is not None:
        return "ok", state["done"], time.time() - start
    return "crash", None, time.time() - start


def summarize(server: Path):
    latest = server / "logs" / "latest.log"
    if latest.exists():
        lines = latest.read_text(encoding="utf-8", errors="replace").splitlines()
        hits = [l for l in lines if re.search(r"/(ERROR|FATAL)\]|Exception|Caused by:", l)]
        seen, uniq = set(), []
        for l in hits:
            key = re.sub(r"^\[[^\]]*\] ", "", l)[:200]
            if key not in seen:
                seen.add(key); uniq.append(l)
        if uniq:
            log(f"ログ内の ERROR／例外（重複除去後 {len(uniq)} 件、先頭 40 件）:")
            for l in uniq[:40]:
                print("   " + l[:300])
        log(f"ログ全文: {latest}")
    crashes = sorted((server / "crash-reports").glob("*.txt")) if (server / "crash-reports").exists() else []
    if crashes:
        log(f"クラッシュレポート: {crashes[-1]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pack")
    ap.add_argument("--accept-eula", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--memory", default="6G")
    ap.add_argument("--keep-world", action="store_true")
    ap.add_argument("--packwiz", default=os.environ.get("PACKWIZ", "packwiz"))
    ap.add_argument("--skip-sync", action="store_true", help="MOD の再取得を省略（設定だけ変えて再テストするとき）")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if not a.accept_eula:
        die("Minecraft EULA（https://aka.ms/MinecraftEULA）への同意が必要です。ユーザーが同意したら --accept-eula を付けてください")
    if not shutil.which(a.packwiz):
        die("packwiz が見つかりません（setup_packwiz.py を実行するか --packwiz でパスを指定）")
    pack_dir = Path(a.pack).resolve()
    mc, loader, lver = read_pack(pack_dir)
    log(f"Minecraft {mc} / {loader} {lver}")
    java_ok()
    server = pack_dir / "run" / "server"
    server.mkdir(parents=True, exist_ok=True)
    gi = pack_dir / ".gitignore"
    if "run/" not in (gi.read_text(encoding="utf-8") if gi.exists() else ""):
        with gi.open("a", encoding="utf-8") as f:
            f.write("run/\n")
    pwi = pack_dir / ".packwizignore"
    if "run/" not in (pwi.read_text(encoding="utf-8") if pwi.exists() else ""):
        with pwi.open("a", encoding="utf-8") as f:
            f.write("run/\n")

    install_neoforge(server, lver) if loader == "neoforge" else install_fabric(server, mc, lver)
    if not a.skip_sync:
        sync_mods(pack_dir, server, a.packwiz)
    prepare_world(server, a.keep_world)
    result, done_at, total = run_server(server, server_command(server, loader, a.memory), a.timeout)
    print()
    if result == "ok":
        log(f"✔ 起動成功（{done_at:.0f} 秒でワールド読み込み完了、合計 {total:.0f} 秒）")
    elif result == "timeout":
        log(f"✘ タイムアウト（{total:.0f} 秒）。読み込みが遅いだけなら --timeout を延ばす")
    else:
        log(f"✘ 起動失敗（{total:.0f} 秒で終了）")
    summarize(server)
    sys.exit(0 if result == "ok" else 1)


if __name__ == "__main__":
    main()
