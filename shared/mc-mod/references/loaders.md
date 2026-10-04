# ローダー別の参照先と API 移行メモ

ここに書いたリポジトリ名・ブランチ名は命名パターンの目安。**必ず `scripts/resolve_ref.sh` で実在を確認してから** refs.conf に書く。

## 目次
1. NeoForge
2. Fabric
3. Forge
4. 依存 MOD の指定
5. 旧バージョンの書き方との対応表

---

## 1. NeoForge
- 雛形: `https://github.com/NeoForgeMDKs/MDK-<MCバージョン>-ModDevGradle`（例: `MDK-1.21.1-ModDevGradle`、ブランチ `main`）。
  NeoGradle 版（`-NeoGradle`）もあるが、特に理由がなければ ModDevGradle を使う。
- ドキュメント: `https://github.com/neoforged/Documentation`（ブランチ `main`）、sparse パス `versioned_docs/version-<MCバージョン>`。
  そのバージョンのフォルダがない場合は最新版が `docs/` にある。ブランチ一覧ではなく中身で確認すること。
- 1.21.1 は NeoForge 21.1.x / Java 21。

## 2. Fabric
- 雛形: `https://github.com/FabricMC/fabric-example-mod`。バージョンごとのブランチ（`1.16.5` など）と `main`（最新）がある。
- ドキュメント: `https://github.com/FabricMC/fabric-docs`（`main`）。
- Fabric API の使い方の見本は、元 MOD が Fabric 版を持っていればそちらが最良。

## 3. Forge
- 新しい Forge の MDK は GitHub リポジトリではなく公式サイトの zip 配布のため、setup_refs.sh の安全方針（github.com のみ）では取得できない。
  ユーザーに NeoForge／Fabric で良いか確認し、Forge が必須なら MDK はユーザー自身に公式サイトから取得してもらう。

## 4. 依存 MOD の指定
優先順:
1. 依存 MOD の README や build.gradle に書かれた公式 Maven
2. 同じ MOD に依存する既存アドオン（同じバージョン）の build.gradle で使われている座標
3. CurseMaven: `curse.maven:<slug>-<projectId>:<fileId>`
4. Modrinth Maven: `maven.modrinth:<slug>:<version>`
確定できなければ CLAUDE.md には「雛形作成時に確認する」と書く。

## 5. 旧バージョンの書き方との対応表（1.7.10／1.12 Forge → 1.20.5 以降）

移植（mc-mod-port）では、CLAUDE.md の「対応方針」に元ソースで実際に使われているものだけ書く。
新規作成（mc-mod-create）では、Web 上のチュートリアルや記憶にある古い書き方を見かけたときの言い換え表として使う。

| 旧 | 新（NeoForge 1.21 系） |
|---|---|
| `GameRegistry.register*`、`@ObjectHolder` | `DeferredRegister` / `DeferredHolder` |
| `cpw.mods.fml.*`（1.7.10）、`net.minecraftforge.fml.*` | `net.neoforged.*` |
| `IIcon`、`registerIcons`（1.7.10） | JSON モデル + blockstate |
| アイテムの NBT（`stackTagCompound` / `getTag`） | Data Components（1.20.5〜） |
| `TileEntity`（1.7.10〜1.12） | `BlockEntity` + `BlockEntityType` |
| `Container` / `GuiContainer` / `IGuiHandler` | `AbstractContainerMenu` / `AbstractContainerScreen` / `MenuType` |
| `SimpleNetworkWrapper` / `IMessage` | `CustomPacketPayload` + `StreamCodec` |
| `Capability` + `@CapabilityInject` | NeoForge 1.21 の Capability（`BlockCapability` 等）、Data Attachments |
| コードでのレシピ登録 | データパック JSON、`RecipeSerializer` |
| `.lang` ファイル | `en_us.json` などの JSON |
| ASM コアモッド（`IFMLLoadingPlugin`） | Mixin（最終手段）。まず API・イベントで代替を探す |
| テクスチャパス `textures/items`、`textures/blocks` | `textures/item`、`textures/block`（小文字・スネークケース） |

Fabric の場合は Mixin が標準の手段だが、Fabric API のイベントで済むならそちらを優先する。
