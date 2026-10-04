# 機能別の参照先と実装時の注意

NeoForge 1.21.1 のドキュメント（`refs/<docs>/versioned_docs/version-1.21.1/`）のパス。他バージョンでも構成はほぼ同じ。
Fabric の場合は fabric-docs の同名トピックを探す。**実装前に該当ページを読むこと。**

## 目次
1. 共通基盤
2. アイテム
3. ブロック・BlockEntity
4. GUI
5. データ（レシピ・ルートテーブル・タグ）
6. 通信・キー操作・config
7. ワールド生成
8. GameTest
9. 見本コードの探し方

---

## 1. 共通基盤
- 登録: `concepts/registries.md`（`DeferredRegister`）
- イベント: `concepts/events.md`（MOD バスとゲームバスの違いに注意）
- サイド: `concepts/sides.md`（クライアント専用コードをサーバーで読み込まない）
- MOD ファイル: `gettingstarted/modfiles.md`
- クリエイティブタブ・言語: `resources/client/i18n.md`
- データ生成: `resources/index.md`。モデル・blockstate・言語・レシピ・ルートテーブルは手書き JSON より datagen を優先

## 2. アイテム
- 基本: `items/index.md`、右クリック等: `items/interactionpipeline.md`
- アイテムごとのデータ: `items/datacomponents.md`（NBT 直書きは使わない）
- 道具・防具: `items/tools.md`
- ポーション効果: `items/mobeffects.md`

## 3. ブロック・BlockEntity
- `blocks/index.md`、状態（向き・ON/OFF）: `blocks/states.md`
- BlockEntity: `blockentities/index.md`、描画: `blockentities/ber.md`
- 保存: `datastorage/codecs.md`、`datastorage/attachments.md`
- アイテム・液体・エネルギーの搬入出: `inventories/capabilities.md`
- 毎ティック処理はサーバー側だけで行い、必要な値だけ同期する

## 4. GUI
- `gui/menus.md` → `gui/screens.md` の順に読む。`MenuType` の登録と、サーバー⇔クライアントでの値の同期（`ContainerData`）がポイント

## 5. データ
- レシピ: `resources/server/recipes/`（特殊なレシピは `RecipeSerializer`）
- ルートテーブル: `resources/server/loottables/`（ブロックを壊してもドロップしない問題の多くはこれの不足）
- タグ: `resources/server/tags.md`（ツールで採掘可能にするには `mineable/*` タグが必要）

## 6. 通信・キー操作・config
- パケット: `networking/payload.md`、`networking/streamcodecs.md`
- キーバインド: `misc/keymappings.md`
- config: `misc/config.md`（SPEC の数値で調整したいものはここへ）

## 7. ワールド生成
- 鉱石・植物の追加: `worldgen/biomemodifier.md`。配置の定義は datagen で出力する

## 8. GameTest
- `misc/gametest.md`。ブロックを置いて N ティック後の状態や数値を検証する
- 実行: `./gradlew runGameTestServer`（タスク名は雛形の build.gradle で確認）
- 目安: 生成量・消費量・変換結果など、数値が SPEC に書かれているものは GameTest を書く

## 9. 見本コードの探し方
ドキュメントで足りないときは、refs に入れた類似 MOD や連携 MOD のソースを `grep -rn "<クラス名>" refs/` で探す。
同じバージョン・同じローダーの、よく使われている MOD のコードが一番信頼できる。
