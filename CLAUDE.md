# nokopi-skills（このリポジトリの保守用メモ）

Claude Code のプラグインマーケットプレイス。`plugins/` 配下にテーマごとのプラグインがあり、各プラグインが 1 つ以上のスキルを持つ。

## 構成
- `.claude-plugin/marketplace.json` — プラグインの一覧（カタログ）
- `plugins/<プラグイン>/.claude-plugin/plugin.json` — 各プラグインの定義（version はプラグインごと）
- `plugins/<プラグイン>/skills/<スキル>/SKILL.md` — スキル本体
- `shared/<プラグイン>/` — 複数のスキルで使う共通ファイルの原本。配布先は `tools/shared.conf`
- `tools/` — 保守用スクリプト（プラグインには含まれない）
- `examples/settings.json` — 新しい環境用の Claude Code 設定例

## ルール
- プラグインはテーマ単位で分ける。無関係なスキルを既存プラグインに混ぜない
- 新しいプラグインは `tools/new_plugin.sh <名前> "<説明>" [スキル名]` で作る（marketplace.json への登録も行う）。作ったら README のプラグイン一覧と `examples/settings.json` にも追記する
- marketplace.json のエントリ名と plugin.json の `name` は必ず同じにする
- 共通ファイルは `shared/` を編集して `tools/sync_shared.sh` で配る。スキル側を直接編集しない。新しい共通ファイルは `tools/shared.conf` に登録する
- スキルに特定の個人・組織固有の情報を書かない（誰でも使えるようにする）。例はプレースホルダーで
- 変更後は `tools/sync_shared.sh --check`、`claude plugin validate .`、`claude plugin validate plugins/<名前>` を通す
- 利用者に更新を届けるときは、変更したプラグインの plugin.json の `version` を上げる
- マーケットプレイス名（`nokopi-skills`）とプラグイン名はインストール ID になるので変更しない
