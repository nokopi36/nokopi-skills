# nokopi-skills

nokopi の [Claude Code](https://code.claude.com/) スキル集（プラグインマーケットプレイス）。
テーマごとのプラグインに分かれているので、必要なものだけインストールできる。

## プラグイン

| プラグイン | スキル | 内容 |
|---|---|---|
| **mc-mod** | `mc-mod-create`, `mc-mod-port` | Minecraft MOD 開発。アイデアから MOD を作る／古い MOD・アドオンを新バージョンへ書き直す（[詳細](plugins/mc-mod/README.md)） |

## インストール

Claude Code のセッション内で、マーケットプレイスを登録してから使いたいプラグインを入れる:

```
/plugin marketplace add nokopi36/nokopi-skills
/plugin install mc-mod@nokopi-skills
```

シェルからなら `claude plugin marketplace add nokopi36/nokopi-skills` → `claude plugin install mc-mod@nokopi-skills`。

更新の取り込み: `/plugin marketplace update nokopi-skills`

### 新しい開発環境でまとめて揃える

[`examples/settings.json`](examples/settings.json) の内容を `~/.claude/settings.json` に入れておくと、マーケットプレイスの登録と有効にするプラグインの指定をまとめて済ませられる。dotfiles で管理しておくと便利。
`enabledPlugins` には、その環境で使うプラグインだけを書く。

## 開発

```bash
tools/new_plugin.sh <名前> "<説明>" [スキル名]   # 新しいプラグインを作って登録
tools/sync_shared.sh                              # 共通ファイルを各スキルへ反映
tools/sync_shared.sh --check                      # ずれの確認（CI でも実行）
claude plugin validate .                          # マーケットプレイスの検証
```

保守のルールは [`CLAUDE.md`](CLAUDE.md)。

## ライセンス
MIT
