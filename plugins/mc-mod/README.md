# mc-mod

Minecraft の MOD 開発を Claude Code で進めるためのプラグイン。

| スキル | 用途 |
|---|---|
| **mc-mod-create** | アイデアの聞き取り → 類似 MOD 調査 → 仕様書（MVP の切り分け）→ プロジェクト作成 → 1 機能ずつ実装・ビルド・テスト・進捗管理 |
| **mc-mod-port** | 古い MOD／アドオンを新しい Minecraft バージョンへ書き直す準備。ソース特定、アドオンなら依存 MOD のバージョンに合わせた移植先の決定、ライセンスと既存移植版の確認、仕様抽出プロンプトの生成 |

どちらも、参考資料（ローダーの雛形・ドキュメント・参考 MOD のソース）を**コミット SHA 固定・取得後に検証**して読み取り専用で取得し、Claude が API を記憶でなく実物で確認しながら書くようにしている。

## 使い方
- 新しく作る: 空のフォルダで Claude Code を起動し、「〇〇な MOD を作りたい」
- 続きから: 作業フォルダで「続きをやろう」（`docs/PROGRESS.md` から再開）
- 移植する: 「<CurseForge／Modrinth／GitHub の URL> の MOD を最新版に移植したい」

## 必要なもの
- git、bash（Windows は Git for Windows 付属の Git Bash）、curl
- 実装には対象バージョンに合う Java（Minecraft 1.21.1 なら Java 21）

Windows の PowerShell から生成されたスクリプトを実行する場合:
`& "C:\Program Files\Git\bin\bash.exe" ./setup_refs.sh`

## 注意
- 権利関係について一般的な注意は促すが、法的助言ではない。他者の MOD を移植・配布する場合は原作者のライセンスと許可を確認すること
- 配布サイトの AI 利用ルール（Modrinth の AI 生成コンテンツ申告など）は変わることがあるので、公開前に最新のルールを確認すること
