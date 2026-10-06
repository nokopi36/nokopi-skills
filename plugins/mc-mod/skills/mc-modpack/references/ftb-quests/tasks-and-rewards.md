# Task & Reward Types Reference

## Task Types

### Item Task (`"item"`)
```snbt
{
	id: "58920EE9A298549B"
	type: "item"
	item: { count: 1, id: "minecraft:copper_ingot" }
	count: 8L
	consume_items: false
}
```
- `item`: object with `id`, optional `count` and `components`
- `count` (long): total items required
- `consume_items` (bool): whether items are consumed on submit

### Checkmark Task (`"checkmark"`)
```snbt
{
	id: "1BF54FD1E2C657FF"
	type: "checkmark"
}
```
Set display label via `task.<ID>.title` in lang file.

### Kill Entity (`"kill"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "kill"
	entity: "minecraft:blaze"
	value: 10L
}
```

### Location (`"location"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "location"
	dimension: "minecraft:overworld"
	position: [100, 64, -200]
	radius: 10L
}
```

### Advancement (`"advancement"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "advancement"
	advancement: "minecraft:story/iron_tools"
}
```

### Dimension (`"dimension"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "dimension"
	dimension: "minecraft:the_nether"
}
```

### Stat (`"stat"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "stat"
	stat: "minecraft:walk_one_cm"
	value: 100000
}
```

### Biome (`"biome"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "biome"
	biome: "minecraft:cherry_grove"
}
```

### Structure (`"structure"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "structure"
	structure: "minecraft:stronghold"
}
```

### Stage (`"stage"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "stage"
	stage: "visited_nether"
}
```

### Fluid (`"fluid"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "fluid"
	fluid: "minecraft:lava"
	amount: 1000L
}
```

### Energy (`"energy"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "energy"
	value: 10000L
}
```

---

## Reward Types

**IMPORTANT:** The `type` field uses plain strings without namespace prefix.
Use `"item"`, `"command"`, `"custom"` — NOT `"ftbquests:item"`.

### Item Reward (`"item"`)
```snbt
{
	id: "7A8A7121B13A9D52"
	type: "item"
	item: { count: 1, id: "minecraft:diamond" }
	count: 16
}
```

### XP Reward (`"xp"`)
```snbt
{
	id: "446F1F89BEB12116"
	type: "xp"
	xp: 500
}
```

### XP Levels Reward (`"xp_levels"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "xp_levels"
	xp_levels: 5
}
```

### Command Reward (`"command"`)
```snbt
{
	id: "3544AB21A43205A8"
	type: "command"
	command: "/advancement grant @p only mymod:power_basics"
	permission_level: 2
}
```
Supports `@p` for the completing player.

### Choice Reward (`"choice"`)
Player chooses one item from a reward table, given in full count.

### All Table Reward (`"all_table"`)
Gives ALL items from a reward table at full count.

### Random Reward (`"random"`)
Picks one random entry. **Always guarantees an item** even if empty weight > 0.

### Loot Reward (`"loot"`)
Standard loot — chance to get item OR nothing (based on empty weight).

### Advancement Reward (`"advancement"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "advancement"
	advancement: "minecraft:story/iron_tools"
}
```
Only grants the specified advancement, not prerequisites. Use command reward with `/advancement grant @p until ...` for the full chain.

### Toast Reward (`"toast"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "toast"
	description: "You unlocked a new area!"
}
```

### Stage Reward (`"stage"`)
```snbt
{
	id: "A1B2C3D4E5F67890"
	type: "stage"
	stage: "visited_nether"
	add: true
}
```

### Custom Reward (`"custom"`)
Does nothing alone — pair with KubeJS.

```snbt
{
	id: "29F9C17B7503E992"
	type: "custom"
}
```

#### KubeJS Integration (requires KubeJS + FTB XMod Compat)

Create `kubejs/server_scripts/my_reward.js`:
```javascript
// CORRECT event name: FTBQuestsEvents.customReward
// NOT FTBQuestsKubeJSEvents — that is wrong
FTBQuestsEvents.customReward('29F9C17B7503E992', event => {
    const level = event.player.experienceLevel
    event.player.give(Item.of('minecraft:diamond', level))
})
```

Reload: `/kubejs reload server-scripts`

#### Stage-Conditional Example
```javascript
FTBQuestsEvents.customReward('082B2A8F0870DB9E', event => {
    const stages = event.player.stages
    if (stages.has('visited_nether')) {
        event.player.give(Item.of('minecraft:diamond', 3))
    } else {
        event.player.give(Item.of('minecraft:diamond', 1))
    }
})
```
