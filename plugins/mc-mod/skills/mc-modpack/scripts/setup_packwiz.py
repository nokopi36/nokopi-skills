#!/usr/bin/env python3
"""
setup_packwiz.py — packwiz を用意する

packwiz は公式のリリースバイナリがないため、Go の公式ツールチェーンで固定コミットからビルドする。
Go のモジュールプロキシとチェックサムデータベース（sum.golang.org）により、依存も含めて改ざんが検出される。

  python setup_packwiz.py [--dest <フォルダ>]   既定: ~/.local/share/mc-modpack/bin

インストール後のパスを表示する。PATH に追加するか、環境変数 PACKWIZ に設定して使う。
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKWIZ_MODULE = "github.com/packwiz/packwiz"
PACKWIZ_COMMIT = "ef87d964f8cbd52b3b13ea42453ef322290e2b9e"  # 2026-10 時点の main。更新するときはここを書き換える


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", default=str(Path.home() / ".local" / "share" / "mc-modpack" / "bin"))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    existing = shutil.which("packwiz")
    if existing:
        print(f"packwiz は既にあります: {existing}")
        return
    if not shutil.which("go"):
        sys.exit("Go が必要です。https://go.dev/dl/ からインストールしてから再実行してください")

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GOBIN": str(dest)}
    # チェックサム検証を弱める設定が環境に入っていても無効にする
    for k in ("GOSUMDB", "GONOSUMDB", "GOPRIVATE", "GONOPROXY", "GOINSECURE", "GOFLAGS"):
        env.pop(k, None)
    print(f"packwiz@{PACKWIZ_COMMIT[:12]} をビルド中…")
    subprocess.run(["go", "install", f"{PACKWIZ_MODULE}@{PACKWIZ_COMMIT}"], env=env, check=True)
    exe = dest / ("packwiz.exe" if os.name == "nt" else "packwiz")
    if not exe.exists():
        sys.exit("ビルドは終わりましたが実行ファイルが見つかりません")
    print(f"完了: {exe}")
    print(f"PATH に {dest} を追加するか、PACKWIZ={exe} を設定してください")


if __name__ == "__main__":
    main()
