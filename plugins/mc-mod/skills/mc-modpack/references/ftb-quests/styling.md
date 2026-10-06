# FTB Quests Theme & Styling Reference

Theme is configured via `ftbquests/ftb_quests_theme.txt` in a resource pack (KubeJS `kubejs/assets/` works too).

**This is a plain text file, NOT JSON or SNBT.** Format is `key: value` lines under `[filter]` sections.

## Property Types

### Color
- `#00A8FF` (RGB hex)
- `#FF00A8FF` (ARGB hex — first 2 are alpha)
- Presets: `transparent`, `black`, `dark_gray`, `gray`, `white`, `red`, `green`, `blue`, `light_red`, `light_green`, `light_blue`

### Icon
- `item:minecraft:diamond` — item icon
- `color:{value}` — solid color as icon
- `bullet:{color}` — bullet point
- `http://...` / `https://...` / `file://...` — remote/local image
- `hollow_rectangle:{color}` — hollow rect
- `part:{icon}` — nine-sliced widget
- `builtin` — mod-internal rendering
- `mymod:textures/gui/foo.png` — direct asset path

#### Icon Modifiers (semicolon + space separated)
```
item:minecraft:diamond; padding=5; border=#00A8FF; border_round_edges=true; tint=#A8FFFFFF
```
Modifiers: `padding={int}`, `border={color}`, `border_round_edges=true`, `color={color}`, `tint={color}`

**The whitespace after `;` is required!**

---

## Full Property List

### Overall
```
background: {icon}
extra_quest_shapes: {comma-separated names}
text_color: {color}
hover_text_color: {color}
disabled_text_color: {color}
```

### Widgets
```
widget_border: {color}
widget_background: {color}
symbol_in: {color}
symbol_out: {color}
button: {icon}
panel: {icon}
disabled_button: {icon}
hover_button: {icon}
context_menu: {icon}
scroll_bar_background: {icon}
scroll_bar: {icon}
container_slot: {icon}
text_box: {icon}
```

### Icons
```
check_icon: {icon}          # default: builtin
add_icon: {icon}            # default: builtin
```

### Quest Book Icons
```
alert_icon, support_icon, wiki_icon, wiki_url, pin_icon_on, pin_icon_off,
editor_icon_on, editor_icon_off, hidden_icon, link_icon, save_icon,
settings_icon, prefs_icon, close_icon, emergency_items_icon, guide_icon,
modpack_icon, reward_table_icon, shop_icon, collect_rewards_icon,
delete_icon, reload_icon, download_icon, edit_icon, move_up_icon, move_down_icon
```
(All icon type)

### Task Specific
```
checkmark_task_active: {icon}
checkmark_task_inactive: {icon}
```

### Quest Window
```
icon: {icon}
full_screen_quest: {int}
tasks_text_color: {color}
rewards_text_color: {color}
quest_view_background: {icon}
quest_view_border: {color}
quest_view_title: {color}
quest_completed_color: {color}
quest_started_color: {color}
quest_not_started_color: {color}
quest_locked_color: {color}
dependency_line_texture: {icon}
dependency_line_completed_color: {color}
dependency_line_uncompleted_color: {color}
dependency_line_requires_color: {color}
dependency_line_required_for_color: {color}
dependency_line_selected_speed: {double}
dependency_line_unselected_speed: {double}
dependency_line_thickness: {double}
quest_spacing: {double}
pinned_quest_size: {double}
left_arrow: {icon}
right_arrow: {icon}
```

---

## Tag-Based Filtering

```
[*]
quest_not_started_color: #FF888888

[boss_quest]
quest_not_started_color: #FFCC2222

[7942A6A571A4C5EB]
quest_not_started_color: #FF00FF00
```

- `[*]` — default for all quests
- `[tagname]` — quests with that tag
- `[hex_id]` — specific quest

Tags > literal IDs for flexibility.

---

## Custom Shapes

1. Add to `extra_quest_shapes: myshape,another`
2. Place textures:
   - `ftbquests:textures/shapes/<name>/background.png`
   - `ftbquests:textures/shapes/<name>/outline.png`
   - `ftbquests:textures/shapes/<name>/shape.png`
3. Translation: `"ftbquests.quest.shape.<name>": "My Shape"`

---

## Variable Substitution

```
quest_completed_color: {{rewards_text_color}}
```

Properties must be compatible types.

## Example Theme File

```
[*]
background: color:#0A1A3A
text_color: #FFFFFFFF
quest_completed_color: #FF22CC44
quest_started_color: #FF5BC0DE
quest_not_started_color: #FF888888
quest_locked_color: #FF444444
dependency_line_completed_color: #FFFFD700
dependency_line_uncompleted_color: #FF666666
dependency_line_thickness: 2.0

[boss_quest]
quest_not_started_color: #FFCC2222
```
