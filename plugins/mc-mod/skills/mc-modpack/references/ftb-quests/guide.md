
# FTB Quests Development Guide

This skill provides comprehensive guidance for creating, editing, and designing FTB Quests configurations for Minecraft modpacks (1.21+). It covers the SNBT file format, directory structure, quest/chapter/reward authoring, visual design, and KubeJS integration.

## Quick Orientation

FTB Quests stores all configuration as **SNBT files** (Stringified NBT) under:

```
config/ftbquests/quests/
├── data.snbt               # Global pack settings
├── chapter_groups.snbt      # Chapter group registry
├── lang/
│   ├── en_us.snbt           # English localization
│   └── zh_cn.snbt           # Chinese localization (or other locales)
└── chapters/
    └── <HEX_ID>.snbt        # One file per chapter (contains all its quests)
```

**Critical rules you must follow:**
- All IDs are **16-character uppercase hex strings** using only characters `0-9` and `A-F` (e.g. `7D7A8EEC0E898ED8`). Never use `G`, `H`, or other non-hex characters.
- Quests live *inside* chapter files, not as separate files
- Localization is separate — quest/chapter titles and descriptions go in `lang/*.snbt`
- Reward `type` values are **plain strings** without namespace prefix: use `"item"`, `"command"`, `"custom"`, NOT `"ftbquests:item"`
- The KubeJS event for custom rewards is `FTBQuestsEvents.customReward()` (NOT `FTBQuestsKubeJSEvents`)

For the full SNBT syntax reference, see `references/snbt-format.md`.
For complete task/reward type specifications, see `references/tasks-and-rewards.md`.
For theme/styling configuration, see `references/styling.md`.

---

## SNBT Syntax — Critical Rules

SNBT is a text serialization of Minecraft's NBT. It looks similar to JSON but has key differences:

```snbt
{
    id: "7942A6A571A4C5EB"
    dependencies: ["6EE7245CA60F0B1C"]
    x: -3.5d
    y: 0.0d
    tasks: [
        {
            id: "58920EE9A298549B"
            type: "item"
            item: { count: 1, id: "minecraft:diamond" }
        }
    ]
    rewards: [
        {
            id: "446F1F89BEB12116"
            type: "xp"
            xp: 500
        }
    ]
}
```

**Syntax rules:**
- **NO commas** between fields at the same nesting level (newline-separated)
- Inline objects on a single line DO use commas: `{ count: 1, id: "minecraft:diamond" }`
- Typed numbers: `0.5d` (double), `128L` (long), `1.0f` (float), `42` (int)
- Strings: double-quoted when containing special characters
- Booleans: `true` / `false` (lowercase)
- Arrays: `[ ]` with entries newline-separated (no commas)

---

## Localization Format

The `lang/*.snbt` file uses **unquoted keys** with colon-space separator. This is NOT JSON:

```snbt
{
	chapter.784A70C90F6F5A49.title: "Getting Started"
	chapter_group.485E071B353FF153.title: "Tutorial"
	quest.7942A6A571A4C5EB.title: "Collect Diamonds"
	quest.7942A6A571A4C5EB.quest_subtitle: "Sparkly!"
	quest.7942A6A571A4C5EB.quest_desc: ["Line 1", "&4Red colored line 2", "Line 3"]
	task.58920EE9A298549B.title: "Custom task label"
}
```

Key patterns:
| Pattern | Purpose |
|---------|---------|
| `chapter.<ID>.title` | Chapter display name |
| `chapter_group.<ID>.title` | Chapter group display name |
| `quest.<ID>.title` | Quest title |
| `quest.<ID>.quest_subtitle` | Quest subtitle (tooltip) |
| `quest.<ID>.quest_desc` | Quest description (string array) |
| `task.<ID>.title` | Task custom label |

Color codes: `&0`-`&f` colors, `&l` bold, `&n` underline, `&o` italic, `&m` strikethrough, `&r` reset.

---

## Global Config: `data.snbt`

```snbt
{
	default_autoclaim_rewards: "disabled"
	default_consume_items: false
	default_quest_disable_jei: false
	default_quest_shape: "circle"
	default_reward_team: false
	detection_delay: 20
	disable_gui: false
	drop_book_on_death: false
	drop_loot_crates: false
	emergency_items_cooldown: 300
	grid_scale: 0.5d
	hide_excluded_quests: false
	lock_message: ""
	loot_crate_no_drop: { boss: 0, monster: 600, passive: 4000 }
	pause_game: false
	progression_mode: "linear"
	show_lock_icons: true
	version: 13
}
```

---

## Chapter File Structure

Each chapter is `chapters/<HEX_ID>.snbt`. The `filename` field MUST match the file name (without `.snbt`):

```snbt
{
	default_hide_dependency_lines: false
	default_quest_shape: ""
	filename: "784A70C90F6F5A49"
	group: "485E071B353FF153"
	icon: { id: "create:wrench" }
	id: "784A70C90F6F5A49"
	images: [ ]
	order_index: 0
	quest_links: [ ]
	quests: [
		{
			id: "7942A6A571A4C5EB"
			dependencies: ["6EE7245CA60F0B1C"]
			x: 0.0d
			y: 0.0d
			tasks: [ ]
			rewards: [ ]
		}
	]
}
```

### Item Icon Format (1.21+)
Simple: `icon: { id: "minecraft:diamond" }`
Custom PNG: `icon: { components: { "ftbquests:icon": "mymod:textures/gui/icon.png" }, id: "ftbquests:custom_icon" }`

---

## Quest Object

```snbt
{
	id: "7942A6A571A4C5EB"
	dependencies: ["6EE7245CA60F0B1C"]
	x: -3.5d
	y: 0.0d
	shape: "circle"
	size: 1.0d
	tasks: [ ]
	rewards: [ ]
}
```

Optional fields (omit to use defaults): `dependency_requirement`, `hide_dependency_lines`, `hide_dependent_lines`, `hide_until_deps_visible`, `invisible_until_completed`, `hide_details_until_startable`, `hide_text_until_complete`, `optional`, `can_repeat`, `progression_mode`, `sequential_tasks`, `disable_jei`, `ignore_reward_blocking`, `icon_scale`, `min_width`.

Dependency requirement modes: `"all_completed"`, `"one_completed"`, `"all_started"`, `"one_started"`.

---

## Task Types Summary

| Type | `type` value | Key fields |
|------|-------------|------------|
| Item | `"item"` | `item: { id: "...", count: 1 }`, `count: 8L`, `consume_items: false` |
| Checkmark | `"checkmark"` | (manual click, set label via lang) |
| Kill Entity | `"kill"` | `entity: "minecraft:blaze"`, `value: 10L` |
| Location | `"location"` | `dimension`, `position`, `radius` |
| Advancement | `"advancement"` | `advancement: "minecraft:story/iron_tools"` |
| Dimension | `"dimension"` | `dimension: "minecraft:the_nether"` |
| Stat | `"stat"` | `stat`, `value` |
| Biome | `"biome"` | `biome` |
| Structure | `"structure"` | `structure` |
| Stage | `"stage"` | `stage` |
| Fluid | `"fluid"` | `fluid`, `amount` |
| Energy | `"energy"` | `value` |

**Item task** — the `item` field is an object with `id` and optionally `count` and `components`. The outer `count` field (long) is the total number required:
```snbt
{
	id: "58920EE9A298549B"
	type: "item"
	item: { count: 1, id: "minecraft:copper_ingot" }
	count: 8L
	consume_items: true
}
```

---

## Reward Types Summary

| Type | `type` value | Key fields |
|------|-------------|------------|
| Item | `"item"` | `item: { id: "..." }`, `count: 16` |
| XP | `"xp"` | `xp: 500` |
| XP Levels | `"xp_levels"` | `xp_levels: 5` |
| Command | `"command"` | `command: "/tp @p ~ ~5 ~"`, `permission_level: 2` |
| Choice | `"choice"` | references reward table |
| All Table | `"all_table"` | references reward table |
| Random | `"random"` | references reward table (always gives item) |
| Loot | `"loot"` | references reward table (chance of nothing) |
| Advancement | `"advancement"` | `advancement: "..."` |
| Toast | `"toast"` | `description: "..."` |
| Stage | `"stage"` | `stage: "..."`, `add: true` |
| Custom | `"custom"` | no-op alone; pair with KubeJS |

### Command Reward
```snbt
{
	id: "3544AB21A43205A8"
	type: "command"
	command: "/advancement grant @p only mymod:power_basics"
	permission_level: 2
}
```

### Custom Reward + KubeJS

1. Add a custom reward in SNBT:
```snbt
{
	id: "29F9C17B7503E992"
	type: "custom"
}
```

2. Create `kubejs/server_scripts/my_reward.js`:
```javascript
// The event name is FTBQuestsEvents.customReward — NOT FTBQuestsKubeJSEvents
FTBQuestsEvents.customReward('29F9C17B7503E992', event => {
    const level = event.player.experienceLevel
    event.player.give(Item.of('minecraft:diamond', level))
})
```

3. Reload: `/kubejs reload server-scripts`

---

## Decorative Images

```snbt
{
	image: "mymod:textures/gui/decoration.png"
	width: 3.0d
	height: 3.0d
	x: -7.0d
	y: 1.5d
	rotation: 0.0d
	order: -1
	hover: ["Tooltip text"]
	click: "https://example.com"
}
```

---

## Reward Tables & Loot Crates

Give loot crate (1.20.5+): `/give @s ftbquests:lootcrate[ftbquests:loot_crate="table_id"]`

Preset rarities (auto-configured when table name matches): `common`, `uncommon`, `rare`, `epic`, `legendary`.

---

## Theme: `ftb_quests_theme.txt`

This is a plain text file placed in a resource pack at `ftbquests/ftb_quests_theme.txt`. It uses `[filter]` sections and `key: value` lines (NOT JSON, NOT SNBT):

```
[*]
background: color:#0A1A3A
quest_completed_color: #FF22CC44
quest_not_started_color: #FF888888
dependency_line_completed_color: #FFFFD700
dependency_line_uncompleted_color: #FFFFD700
dependency_line_thickness: 2.0

[boss_quest]
quest_not_started_color: #FFCC2222
```

- `[*]` applies to all quests (fallback defaults)
- `[tagname]` applies to quests tagged with that name
- `[hex_quest_id]` applies to a specific quest

See `references/styling.md` for the full property list.

---

## Commands

| Command | Description |
|---------|-------------|
| `/ftbquests reload` | Reload config and quests |
| `/ftbquests editing_mode [true\|false] [player]` | Toggle editing mode |
| `/ftbquests change_progress <player> <reset\|complete> <quest_id>` | Complete/reset quest |
| `/ftbquests change_progress <player> <reset-all\|complete-all>` | Complete/reset all |
| `/ftbquests open_book [quest_id]` | Open quest book |

---

## Design Best Practices

1. **Plan layout first** — sketch quest positions on a grid before writing SNBT
2. **Valid hex IDs only** — 16 chars, `0-9` and `A-F` only. Never use `G`-`Z`.
3. **Leverage chapter defaults** — set shapes, consume_items at chapter level
4. **Progressive visibility** — use `hide_until_deps_visible` to avoid overwhelming players
5. **Localize everything** — keep all text in `lang/` files using `key: "value"` format
6. **Hot reload** — use `/ftbquests reload` to test changes without restart
7. **Command rewards for chaining** — use `/ftbquests change_progress` to unlock hidden quests
