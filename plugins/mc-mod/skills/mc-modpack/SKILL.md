---
name: mc-modpack
description: Minecraft のモッドパックを作るスキル。コンセプトの聞き取り、バージョンとローダーの決定、Modrinth API での MOD 選定と依存・非互換・動作側の検査、packwiz での組み立て、専用サーバーでの自動起動テストとクラッシュ原因の特定、設定・レシピ調整、FTB Quests のクエスト作成（アイテム ID の実在検証つき）、.mrpack／CurseForge 形式への書き出しまでを行う。「モッドパックを作りたい」「〇〇系の MOD を集めて遊びたい」「身内サーバー用のパックを組みたい」「クエストを作って」「パックが起動しない」など、モッドパックの作成・調整・クエスト作成の話が出たら必ずこのスキルを使うこと。MOD そのものを作る話は mc-mod-create、既存 MOD の移植は mc-mod-port を使う。
---

# MC モッドパック作成

**基本方針: 少なく入れて、毎回起動する。** MOD は役割ごとに選び、追加のたびに検査と起動テストを回す。
クエストはパックの中身が固まってから作る。

## まず状態を判定する

| 作業フォルダの状態 | 開始フェーズ |
|---|---|
| 何もない | 1 |
| `docs/PACK.md` はあるが `pack.toml` がない | 4 |
| `pack.toml` と `docs/PROGRESS.md` がある | `PROGRESS.md` を読んで続きから |

再開時は「前回は○○まで、次は△△」と一言確認してから進む。

**必要な環境**: Python 3.11 以上、Java（Minecraft のバージョンに合うもの。1.21.1 なら 21）、packwiz。
シェルが使えない環境ではフェーズ 3（MOD 選定の提案）まで行い、続きは Claude Code でと案内する。
スクリプトは `python scripts/<名前>.py`（Windows で `python` がなければ `py`）で実行する。

---

## フェーズ 1: コンセプト
一度に全部聞かず、答えに合わせて掘り下げる。
1. どんなパックか一言で（工業、魔術、冒険、探索、バニラ＋α、スカイブロック など）
2. ソロか、身内マルチ（人数）か、公開か
3. 好きな MOD・遊んだことのあるパック、入れたい MOD
4. PC のスペック（メモリ、GPU）。身内サーバーならサーバーのスペックも
5. 遊びの流れ — 何を目標に進めるか。クエストを入れるか

## フェーズ 2: 土台
- 入れたい中心 MOD があれば、その対応状況（`scripts/modrinth.py info <slug> --mc <版> --loader <ローダー>`）から Minecraft のバージョンとローダーを決める
- なければ、MOD が最も揃っているバージョンを提案する（最新状況は検索や API で確認し、記憶で決めない）
- ローダーのバージョンは、そのとき推奨されている安定版を確認して決める

## フェーズ 3: MOD 選定
`references/modpack.md` の 2・3 章に従う。
- 役割ごとに候補を `modrinth.py search` で探し、`modrinth.py info` で対応版・依存・非互換・動作側・ライセンスを確認
- 役割・候補・推奨・理由を表で提示し、ユーザーに選んでもらう。**最初は 20〜40 個程度**に抑えることを勧める
- 決まった内容を `assets/PACK.template.md` から作った `docs/PACK.md` に書く（入れた理由・見送った理由も）

## フェーズ 4: 組み立て
1. packwiz がなければ `scripts/setup_packwiz.py` で用意する（Go が必要。固定コミットからビルド）
2. `packwiz init` → `.packwizignore` に `run/`、`docs/`、`CLAUDE.md`、`.git*` を入れる
3. `docs/PACK.md` の MOD を packwiz で追加（Modrinth 優先）。依存の追加は承諾する。対応版がなければ勝手に代替せず報告
4. side を確認（クライアント専用の描画・UI 系は `client`）
5. `scripts/modrinth.py check .` で不足依存・非互換・side の食い違いを検査し、解消する
6. `assets/CLAUDE.md.template` から `CLAUDE.md`、`assets/PROGRESS.template.md` から `docs/PROGRESS.md` を作り、`git init` してコミット

## フェーズ 5: 起動テスト
1. **Minecraft EULA（https://aka.ms/MinecraftEULA）への同意をユーザーに確認する。** 同意が得られたら以後のテストで `--accept-eula` を付けてよい
2. `scripts/boot_test.py . --accept-eula` を実行。初回はローダーのサーバーと MOD の取得で時間がかかる
3. 失敗したら、表示された ERROR とクラッシュレポートを読み、原因の MOD を特定する（`references/modpack.md` 5 章）。
   直し方（版の変更・MOD の削除・設定変更）を提案し、承認後に直して再テスト。**成功するまで繰り返す**
4. 成功したら、ランチャー（Prism Launcher、Modrinth App など）でのクライアント起動確認の手順を渡す。
   `packwiz modrinth export` した `.mrpack` を読み込むのが手軽
5. 結果を `docs/PROGRESS.md` の起動テスト履歴に記録してコミット

## フェーズ 6: 調整
- 素材の重複、レシピの衝突、難易度などをユーザーと相談して、config や KubeJS で調整する（`references/modpack.md` 4 章）
- 変更のたびに `packwiz refresh` → 起動テスト。理由を `docs/PACK.md` の「調整」に残す
- MOD の追加・削除の要望はフェーズ 3〜5 の手順で行う

## フェーズ 7: クエスト（FTB Quests）
1. `references/ftbquests-versions.md` を読み、入っている FTB Quests のバージョンと保存形式を確認する。1.21 系以外は実物で形式を確かめる
2. 1.21 系なら `references/ftb-quests/guide.md`、`snbt-format.md`、`tasks-and-rewards.md` を読む（見た目の調整は `styling.md`）
3. **進行の設計を先に出して承認をもらう**: チャプター構成、各チャプターの目標、主要クエストと依存の流れ、報酬の方針。
   パック内の MOD の実際のアイテム・レシピに沿って組む（入っていない MOD のアイテムを使わない）
4. `scripts/quests.py items .` でアイテム一覧を作り（起動テスト済みであること）、使うアイテムは `quests.py find . <語>` で実在を確認してから書く
5. ID は `quests.py newid <個数> --pack .` で生成する。手で作らない
6. 1 チャプターずつ書く。日本語と英語の両方の lang ファイル（`ja_jp.snbt`、`en_us.snbt`）を用意する
7. `quests.py validate .` でエラーがなくなるまで直し、`packwiz refresh` → 起動テスト
8. ゲーム内で見た目（配置）を確認してもらう。ユーザーがゲーム内で配置を直した場合は、そのファイルをパックに戻してもらい、読み直してから次のチャプターへ

## フェーズ 8: 書き出し
- `packwiz modrinth export`／`packwiz curseforge export`
- 公開する場合は `references/modpack.md` 6 章の確認（ライセンス・再配布可否・配布先ルール）をユーザーと一緒に行う。法的判断は断定せず、私は弁護士ではないと添える
- 身内用なら、packwiz-installer による自動更新の配布方法も案内できる

## トラブル時
- 同じ原因で 3 回直しても起動しない場合は、状況（エラー、試したこと、候補）をまとめてユーザーに相談する
- MOD の不具合が疑われる場合は、その MOD の Issue を検索し、既知の問題か確認する

## 参照ファイル
- `scripts/modrinth.py` — MOD の検索・情報・パック全体の依存／非互換検査
- `scripts/setup_packwiz.py` — packwiz を固定コミットからビルド
- `scripts/boot_test.py` — 専用サーバーでの起動テスト（ローダー・ブートストラップはチェックサム照合）
- `scripts/quests.py` — クエスト ID 生成、アイテム一覧の作成と検索、クエストファイルの検証
- `references/modpack.md` — packwiz、MOD の選び方、衝突の対処、調整、起動テスト、配布
- `references/ftbquests-versions.md` — FTB Quests のバージョン別の保存形式
- `references/ftb-quests/` — FTB Quests 1.21 系の詳細資料（ParticleG/ftb-quests より、MIT。`NOTICE.md` 参照）
- `assets/PACK.template.md` / `PROGRESS.template.md` / `CLAUDE.md.template`
