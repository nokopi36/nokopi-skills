# モッドパック作成メモ

## 目次
1. packwiz の基本
2. MOD の選び方
3. よくある衝突と対処
4. 設定・レシピの調整
5. 起動テストで見るところ
6. 書き出しと配布

---

## 1. packwiz の基本
- **Claude Code からは対話プロンプトに答えられない**ので、引数を指定し、必要なら `-y`（全プロンプトに既定値／yes で答える）を付ける。
  `-y` は検索結果から意図しない MOD を選ぶことがあるので、追加は slug か URL で正確に指定する
- 初期化: `packwiz init --name <名前> --author <作者> --version <パックの版> --mc-version <MC版> --modloader <neoforge|fabric> --<ローダー>-version <版>`
- 追加: `packwiz modrinth add <slug|URL>`（短縮 `packwiz mr add`）、`packwiz curseforge add <slug|URL>`（`packwiz cf add`）
  - 依存 MOD も追加するか聞かれる。基本は追加する
  - 対応版がない場合はエラーになる。勝手に別バージョンの版を入れない
- 更新: `packwiz update <名前>`、`packwiz update --all`
- 削除: `packwiz remove <名前>`
- 索引の更新: `packwiz refresh`（config などを手で追加・編集したら必ず実行）
- 配信（テスト用）: `packwiz serve`
- 各 MOD は `mods/<名前>.pw.toml`。`side = "both" | "client" | "server"` でどちら側に入るかが決まる
- パックに含めたくないファイルは `.packwizignore`（書式は .gitignore と同じ）。`run/`、`docs/` などは必ず入れる
- コマンドの細かい引数は `packwiz <コマンド> --help` で確認する（記憶で書かない）

## 2. MOD の選び方
- 取得元は可能な限り **Modrinth を優先**（API で依存・非互換・動作側が分かり、`modrinth.py check` で検査できる）。Modrinth にないものだけ CurseForge
- 判断材料: 対象バージョン・ローダーの対応版があるか、最終更新、ダウンロード数、ライセンス、client_side / server_side
- **役割で考える**: 「鉱石と金属」「ストレージ」「自動化」「冒険（構造物・ボス）」「QoL」「最適化」「ワールド生成」など、
  役割ごとに 1 つ（多くても 2 つ）に絞る。同じ役割の大型 MOD を重ねると、素材が重複してバランスが崩れる
- **最適化 MOD** はスペックの答えに合わせて入れる。ローダーごとに定番が違うので、その都度 Modrinth で対応状況を確認する
- 迷ったら少なく。あとから足すのは簡単で、抜くのはワールドが壊れる

## 3. よくある衝突と対処
- **同じ素材が複数の MOD から出る**（銅・錫・鉛など）: 統一系 MOD（例: タグで素材をまとめるもの）を入れるか、KubeJS で一方のレシピ・ワールド生成を止める
- **同じ機能の重複**（ミニマップ 2 つ、レシピビューア 2 つ）: 片方を外す
- **ワールド生成の過密**: 構造物 MOD を入れすぎると探索が単調になり、生成も重くなる
- **起動時の衝突**: Mixin の衝突や依存の版違いはクラッシュレポートに MOD 名が出る。まず該当 MOD の版を確認し、Modrinth のバグ報告も検索する

## 4. 設定・レシピの調整
- 設定ファイルは `config/`（一部の MOD は `defaultconfigs/` やワールドごとの `serverconfig/`）。初回起動で生成されたものを `run/server/config/` からパックへコピーして編集し、`packwiz refresh`
- レシピの追加・削除・置き換えは KubeJS（`kubejs/server_scripts/`）が定番。KubeJS 自体の書き方はバージョンで大きく変わるので、入っている版のドキュメントを確認する
- 変更のたびに起動テストで読み込みエラーがないか確認する

## 5. 起動テストで見るところ
- `✔ 起動成功` でも、ログに ERROR が大量に出ていれば調べる。特に「Failed to load」「Mixin apply failed」「Missing」「Unknown recipe」
- クラッシュレポートでは「Suspected Mod(s)」「Caused by:」の行を最初に見る
- 専用サーバーではクライアント専用 MOD（描画・UI・最適化系の一部）は読み込まれない。最後は必ずランチャーでクライアント起動も確認する
- 重い場合は `--memory` を増やす前に、MOD 数と構造物 MOD を見直す

## 6. 書き出しと配布
- Modrinth 形式: `packwiz modrinth export` → `.mrpack`。CurseForge 形式: `packwiz curseforge export` → `.zip`
- **配布する場合**:
  - 各 MOD のライセンスと再配布可否を確認する。CurseForge では作者が外部配布を禁止している MOD があり、Modrinth 形式のパックに入れられないことがある
  - Modrinth のモッドパックで Modrinth 外のファイルを含めるには、作者の許可が必要になる場合がある。公開前に最新のルールを確認する
  - 配布先の AI 利用ルール（Modrinth の AI 生成コンテンツ申告など）も確認する
- 身内用なら、`packwiz serve` や GitHub Pages で `pack.toml` を配信し、各自が packwiz-installer で自動更新する運用も便利
