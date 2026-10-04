---
name: mc-mod-port
description: Minecraft の MOD／アドオンを新しい Minecraft バージョンへ移植・書き直しするための準備を進めるスキル。CurseForge や Modrinth のページ（または GitHub URL）からソースを特定し、ライセンスと既存の移植版を確認し、アドオンなら元 MOD のバージョンに合わせて移植先を決め、参考資料をコミット固定で安全に取得するスクリプト・CLAUDE.md・仕様抽出プロンプトを生成する。「この MOD を 1.21 にしたい」「古いバージョンしかない MOD を最新版で遊びたい」「アドオンを移植したい」「MOD をアップデート／ポートしたい」など、MOD のバージョン更新・移植・リメイクの話が出たら、MOD 名や URL だけでも必ずこのスキルを使うこと。
---

# MC MOD 移植キット作成

古いバージョンの MOD／アドオンを、Claude Code で新バージョン向けに書き直すための「キット」を作る。
キットの中身は、参考資料取得スクリプト（`setup_refs.sh` + `refs.conf`）、`CLAUDE.md`、仕様抽出・実装プロンプト。
**このスキル自身は移植コードを書かない。** 仕様抽出と実装はキットを使った後続の作業で行う。

## 全体の流れ

1. 対象の特定（ページ → GitHub）
2. 種別の確認（単体 MOD／アドオン）と、アドオンなら元 MOD の特定
3. 移植先バージョンとローダーの決定（質問する）
4. ライセンス・既存移植版の確認（質問する）
5. 参照リポジトリの解決とコミット固定
6. キット生成と検証
7. 次の手順の案内

質問は一度にまとめすぎない。各ステップで分からないことだけ聞き、分かったことは確認として短く伝える。

---

## 1. 対象の特定

入力は CurseForge URL、Modrinth URL、GitHub URL、MOD 名のいずれか。

- **GitHub URL**: そのまま使う。
- **Modrinth**: `https://api.modrinth.com/v2/project/<slug>` の `source_url`・`license`・`game_versions`・`loaders` が使える。
- **CurseForge**: ページは Cloudflare で弾かれて取得できないことが多い。取得できたら説明文やサイドバーの「Source」リンクを探す。取れなければ「<MOD 名> github」で検索し、作者名・MOD ID・パッケージ名が一致するか確認する。それでも見つからなければユーザーに GitHub URL を聞く。
- 見つけたリポジトリが本当に同じ MOD か（作者名、`mcmod.info`／`mods.toml`／`fabric.mod.json` の modid）を確認してから進む。CurseForge の配布者がフォーラム作者の転載者であるケースもあるので、**原作者**を特定しておく（ライセンス判断に必要）。
- ソースが公開されていない場合は、jar の逆コンパイルではなく「公開情報（説明文・Wiki・動画）から仕様を書き起こす」方針になることを伝え、続行するか聞く。

`git ls-remote --heads <url>` でブランチ一覧を取り、どのブランチが対象バージョンかを把握する。

## 2. 単体 MOD かアドオンか

ソースの依存関係（`build.gradle`、`mcmod.info` の `dependencies`、`@Mod(dependencies=...)`、`mods.toml`、`fabric.mod.json` の `depends`）を見て判断する。

- 他 MOD の API を使っている、または ASM／Mixin で他 MOD を書き換えているならアドオン。
- 判断できたら確認として伝える。依存先が複数あるときや判断できないときは「元となる MOD はどれか」を聞く。
- アドオンの場合、元 MOD の GitHub も特定する（手順 1 と同じ方法）。

**ASM コアモッド（`IFMLLoadingPlugin`、`IClassTransformer`）や Mixin で元 MOD を書き換えている箇所は、移植の最難所**なので、見つけたら必ずユーザーに伝え、仕様書で重点的に扱うようにする。

## 3. 移植先バージョンとローダー

### アドオンの場合
バージョンは**元 MOD に合わせる**。元 MOD のリポジトリのブランチ（`mc1.21.1`、`1.21`、`1.20.x` など）、Modrinth の `game_versions`、リリースタグから、元 MOD が対応している新しいバージョンを列挙する。
そのうえで「最新（例: 1.21.1）にするか、特定のバージョンにするか」を聞く。元 MOD が対応していないバージョンは選択肢に出さない。
ローダーも元 MOD が対応しているもの（NeoForge／Fabric など）に限られる。複数あれば聞く。

### 単体 MOD の場合
「最新の Minecraft にするか、特定のバージョンにするか」を聞く。ローダー（NeoForge／Fabric／Forge）も聞く。
一緒に遊びたい他の MOD があるならそれに合わせるのが安全、と一言添える。

### 注意
- 「1.21」のような曖昧な指定は、実際に元 MOD やローダーが対応しているパッチバージョン（1.21.1 等）に具体化して確認する。MOD はパッチバージョンが違うと基本的に動かない。
- 最新状況は記憶ではなく `git ls-remote` や API で確認する。

## 4. ライセンスと既存の移植版

### ライセンス
対象（と元 MOD）の LICENSE ファイル、配布ページのライセンス表記を確認し、結果をユーザーに伝える。
そのうえで **私的利用か、公開予定か** を聞く。答えで CLAUDE.md の「ライセンスと利用範囲」セクションが変わる。

- ライセンス表記なし／ARR／Custom: 権利は作者にある。私的利用ならアセット流用可、公開ならアセット自作か作者の許可が必要。
- OSS ライセンス（MIT、LGPL など）: 条件（表記・同一ライセンス等）を CLAUDE.md に書く。
- どちらの場合もコードは旧バージョンのものを直接コピーしない（API が違い動かないため）。仕様を参照して再実装する。
- 公開予定の場合は、配布先の AI 利用ルールにも触れる（Modrinth は 2026-08 から AI 生成コードの申告が必須で、ほぼ AI 製のプロジェクトは検索に出ない。CurseForge はコードについての規定なし）。最新ルールは確認すること。

法的判断は断定せず、私は弁護士ではないと添える。

### 既存の移植版
「<MOD 名> <移植先バージョン>」「<MOD 名> port」「<MOD 名> remake／reborn／continued」などで CurseForge・Modrinth・GitHub を検索する。
見つかったら、対応バージョン・実装済みの機能範囲・最終更新・ライセンスを調べ、可能ならソースを取得して実装範囲を確認する。結果を伝え、
「それを使う／足りない機能だけ自作して併用する（modid を分ける）／全部自作する」のどれにするか聞く。
併用する場合は、仕様抽出プロンプトから既存版がカバーする機能を除外する。

## 5. 参照リポジトリの解決

`refs.conf` に入れる参照先を決める。基本セット:

| 名前 | 内容 |
|---|---|
| 対象 MOD | 移植元のソース（旧バージョンのブランチ） |
| 元 MOD（アドオンの場合） | **移植先バージョン**のブランチ。正しい書き方の見本になる |
| ローダーの雛形 | `references/loaders.md` 参照 |
| ローダーのドキュメント | 対象バージョンの部分だけ sparse で |
| 既存の移植版（あれば、参考用） | ライセンスに関わらず読むだけ。コピーしない |

各リポジトリのコミット SHA は `scripts/resolve_ref.sh <url> <branch>` で取得する（`git ls-remote` を呼ぶだけで何も実行しない）。
存在しないブランチやリポジトリを推測で書かないこと。

元 MOD の依存座標（Maven／CurseMaven／Modrinth Maven）が分かれば CLAUDE.md に書く。分からなければ「雛形作成時に確認する」と書いておく。

## 6. キット生成

出力先ディレクトリ（例: `<作業フォルダ>/<modname>-port-kit/`）に以下を作る。

1. `scripts/setup_refs.sh` をそのままコピー（実行権限を付ける）
2. `refs.conf` を作成（形式は setup_refs.sh 冒頭のコメント参照）
3. `assets/CLAUDE.md.template` を元に `CLAUDE.md` を作成し、`{{...}}` をすべて埋める。不要なセクション（単体 MOD なら元 MOD 関連）は削除し、ASM／Mixin の有無、ライセンス方針、既存版との併用方針を反映する
4. `assets/prompts/` の 2 ファイルを `prompts/` にコピーし、`{{...}}` を埋める。仕様抽出プロンプトの「必ず詳細に書く対象」には、実際にソースを見て分かった主要機能を列挙する
5. `README.md`（手順と、Windows の場合は Git Bash から実行する旨）

可能なら生成後に `./setup_refs.sh` → `./setup_refs.sh --verify` を実行して取得とSHA検証が通ることを確認し、`refs/` は削除してから渡す。
`{{` が残っていないことを grep で確認する。

## 7. 案内

最後に短く伝える:
- 実行方法（Windows の PowerShell なら `& "C:\Program Files\Git\bin\bash.exe" ./setup_refs.sh`）
- 次の手順: Claude Code で `prompts/01_extract_spec.md` → SPEC をレビュー → 雛形からプロジェクト作成 → `prompts/02_implement_feature.md` で 1 機能ずつ
- 移植の難所（ASM／Mixin、大きな API 変更点）と、決めたライセンス方針

## 参照ファイル
- `scripts/setup_refs.sh` — 汎用の参考資料取得スクリプト（refs.conf を読む）
- `scripts/resolve_ref.sh` — ブランチ名からコミット SHA を解決
- `assets/CLAUDE.md.template` — キット用 CLAUDE.md の雛形
- `assets/prompts/01_extract_spec.md`, `02_implement_feature.md` — プロンプト雛形
- `references/loaders.md` — ローダー別の雛形・ドキュメントの所在と、旧バージョンからの主な API 変更点。手順 5・6 で読む
