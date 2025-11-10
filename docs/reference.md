---
layout: default
title: Quick Reference
nav_order: 3
---

# Quick Reference

Fast lookup tables for controls, parameters, and MIDI mappings.

> **💡 Tip**: Bookmark this page for quick access, or print it as a cheat sheet!

---

## Table of Contents

- [Controls & Shortcuts](#controls--shortcuts)
- [All Parameters](#all-parameters)
- [VSN1 MIDI Mappings](#vsn1-midi-mappings)
- [Grid Editor Package Preferences](#grid-editor-package-preferences-vsn1-only)

---

## Controls & Shortcuts

Complete reference for all hardware controls and keyboard shortcuts.

| Control | Action | Notes |
|---------|--------|-------|
| **Basic Controls** | | |
| Twist knob | Adjust hovered/active parameter | Step size affects increment |
| Push knob | Pulse/toggle parameter | Works with Pulse, Momentary, Toggle types |
| Press step button | Change step size | Cycles through 0.001, 0.01, 0.1, 1 (default) |
| **Slot Operations** | | |
| Press slot button | Activate slot / Return to hover | Press empty slot to exit slot mode |
| Long-press slot button (hovering) | Assign parameter to slot | 500ms default hold time |
| Long-press slot button (no hover) | Clear slot assignment | Removes parameter from slot |
| Long-press slot button (slot active) | Reassign slot | New parameter overwrites existing |
| Push knob + slot button | Jump to operator | Opens network at parameter's operator |
| **Bank Switching** | | |
| Long-press step button | Switch to that bank | Each bank = independent slots |
| **Step Modes** | | |
| Leftmost + rightmost step buttons | Toggle Fixed/Adaptive mode | Changes step calculation method |
| Push knob + step button | Set alternate push step | Only in "Fixed" push mode |
| Push knob + twist | Use alternate precision | Behavior depends on Push Step Mode |
| **Parameter Shortcuts** | | |
| First + second button | Reset to default | Restores parameter's default value |
| First + third button | Set current as default | Makes current value the new default |
| Second + third button | Set current as min | Sets normMin and min to current value |
| Second + fourth button | Set current as max | Sets normMax and max to current value |
| Third + fourth button | Clamp to range | Brings value within min/max bounds |
| First + fourth (long-press) | Open component editor | Opens active parameter's operator, or selected COMP if none |
| **Keyboard Shortcuts** | | |
| `Ctrl+Z` / `Cmd+Z` | Undo last action | Works on params, slots, resets, etc. |
| `Ctrl+Y` / `Cmd+Shift+Z` | Redo action | Restores undone operations |
| **Network Zoom** (when enabled & no active parameter) | | |
| Twist knob clockwise | Zoom in + pan to cursor | Seek or Target mode (configurable) |
| Twist knob counter-clockwise | Zoom out + pan | Works until zoom limit (3x) |
| Push knob | Zoom in fast | Larger zoom increment per twist |

> **Button References**: "First" = leftmost, "Second" = second from left, etc. On VSN1: step buttons are under LCD, slot buttons are the 8 clicky keyboard buttons.

---

## All Parameters

Complete parameter reference organized by category.

| Parameter | Description | Default |
|-----------|-------------|---------|
| **General** | | |
| `Active` | Enable/disable entire component | On |
| `MIDI Status` | Shows MIDI connection state (read-only) | - |
| `Connected Status` | Shows websocket connection state (read-only) | - |
| `Reinit` | Pulse to reinitialize component | - |
| **Step Configuration** | | |
| `Step Mode` | "Fixed" or "Adaptive" precision | Fixed |
| `Push Step Mode` | "Fixed", "Finer", or "Coarser" | Fixed |
| `Push Step` | Current push step value (read-only) | - |
| `Steps[0-3] Index` | MIDI index for step buttons | 40-43 |
| `Steps[0-3] Step` | Step size value | 0.001-1 |
| **Parameter Behavior** | | |
| `Loop Menus` | Menu parameters wrap around | Off |
| `Control StrMenus` | Allow string-menu parameter control | Off |
| **Undo System** | | |
| `Enable Undo` | Enable undo/redo functionality | On |
| `Undo Timeout` | Delay before pushing value changes to stack (sec) | 1 |
| **Shortcuts** | | |
| `Shortcuts` | Enable button combo shortcuts | On |
| `Slot Learn Hold Length` | Long-press duration for slot assignment (ms) | 500 |
| `Bank Switch Hold Length` | Long-press duration for bank switching (ms) | 500 |
| `Reset Hold Length` | Long-press duration for parameter reset (ms) | 500 |
| `Min/Max Clamp Hold Length` | Long-press duration for clamp operations (ms) | 500 |
| `Customize Hold Length` | Long-press for component editor jump (ms) | 500 |
| **Hover Timeout** | | |
| `Hover Timeout Length` | Seconds parameter stays active after unhover | 0 |
| `Sticky Par` | MIDI adjustments restart timeout countdown | Off |
| **Storage** | | |
| `Slots Repo` | Reference to external storage table | - |
| `Auto Create Repo` | Automatically create external repo on init | On |
| `Create Repo` | Pulse to manually create external repo | - |
| **VSN1 Integration** | | |
| `VSN1 Support` | Enable VSN1 screen/LED feedback | On |
| `Start Grid Editor` | Pulse to launch Grid Editor | - |
| `Auto Start Grid Editor` | Launch Grid Editor on TD startup | Off |
| `Net Address` | Websocket address | localhost |
| `Port` | Websocket port | 9642 |
| `Periodic Reconnect` | Attempt periodic reconnection | On |
| `Reconnect Period` | Reconnection interval (sec) | 5 |
| `Reset Comm` | Pulse to reset websocket connection | - |
| `Knob LED Update` | LED mode: "Off", "Value", or "Step" | Value |
| `Label Display Mode` | "Compressed" or "Truncated" | Compressed |
| **UI Settings** | | |
| `TD UI` | Enable internal UI display | On |
| `Enable UI` | Alias for TD UI | On |
| `Enable UI Color` | Color-highlight hovered parameters in TD | On |
| `Hide Author Label` | Hide author name from UI | Off |
| `Bloom` | Enable bloom effect on UI | Off |
| `Color Hovered UI` | Apply color to hovered UI elements | On |
| `Color Index` | Color palette index for UI | 1 |
| `General UI Settings` | UI configuration section header | - |
| `Show Builtin Pars` | Show built-in TD parameter pages | Off |
| **Network Zoom** | | |
| `Activate on Jump` | Activate parameter when jumping to operator | Off |
| `Use Current Zoom` | Maintain current zoom level on jump | On |
| `Enable Zoom` | Enable network editor zoom navigation | Off |
| `Zoom Mode` | "Seek" (follow cursor) or "Target" (lock) | Seek |
| `Zoom Network` | Zoom speed per knob increment | 0.015 |
| `Zoom Interpolation` | Camera movement smoothness (0.0-1.0) | 0.015 |
| **MIDI Configuration** | | |
| `Device ID` | MIDI device identifier | 0 |
| `Channel` | MIDI channel | 0 |
| `Learn` | Enter MIDI learn mode | - |
| `Clear` | Clear learned MIDI mappings | - |
| `Use Defaults for VSN1` | Load default VSN1 MIDI mappings | - |
| `Knob Index` | MIDI CC index for main knob | 32 |
| `Push Index` | MIDI CC index for knob push button | 36 |
| **Slot Mappings** | | |
| `Slots[0-7] Index` | MIDI index for slot buttons | 44-51 |
| **Bank Mappings** | | |
| `Banks[0-3] Index` | MIDI index for bank buttons | 40-43 |
| **About** | | |
| `Author Name` | Component author (read-only) | Function Store |
| `Open Author` | Open author website | - |
| `Open Help` | Open documentation site | - |
| `Version` | Current version (read-only) | - |
| `Check` | Check for updates | - |
| `Update` | Download and install update | - |
| `Externalize Component` | Save to palette and externalize repo | - |

> **💡 Parameter Help**: Hover over any custom parameter in the component while holding **Alt** (or **Option** on Mac) to see detailed help text.

---

## VSN1 MIDI Mappings

Default MIDI CC mappings for Intech Studio VSN1 hardware.

| Control | MIDI CC | Type | Notes |
|---------|---------|------|-------|
| **Encoders** | | | |
| Main Knob (twist) | 32 | Relative | Endless encoder, sends relative values |
| Main Knob (push) | 36 | Momentary | Button press on knob |
| **Step Buttons** (under LCD) | | | |
| Step 0 | 40 | Toggle | Also used for bank switching (long-press) |
| Step 1 | 41 | Toggle | Also used for bank switching (long-press) |
| Step 2 | 42 | Toggle | Also used for bank switching (long-press) |
| Step 3 | 43 | Toggle | Also used for bank switching (long-press) |
| **Slot Buttons** (clicky keyboard) | | | |
| Slot 0 | 44 | Toggle | With LED feedback |
| Slot 1 | 45 | Toggle | With LED feedback |
| Slot 2 | 46 | Toggle | With LED feedback |
| Slot 3 | 47 | Toggle | With LED feedback |
| Slot 4 | 48 | Toggle | With LED feedback |
| Slot 5 | 49 | Toggle | With LED feedback |
| Slot 6 | 50 | Toggle | With LED feedback |
| Slot 7 | 51 | Toggle | With LED feedback |

### MIDI Configuration Notes

- **Device ID**: Default is `0`, match this with TouchDesigner's MIDI Device Mapper
- **Channel**: Default is `0` (MIDI Channel 1)
- **Relative Encoding**: Knob uses relative/endless encoding (not absolute 0-127)
- **LED Feedback**: Slot buttons receive LED state updates via MIDI
- **Screen Updates**: VSN1 screen controlled via websocket (port 9642), not MIDI

### Custom MIDI Controllers

For other MIDI controllers with endless encoders:
1. Use **MIDI Learn** (`Learn` parameter pulse, or long-press slots 0+7)
2. Map your knob and buttons to the component
3. Adjust `Device ID` and `Channel` as needed
4. See [Advanced Guide](advanced.html#manual-midi-mapping) for detailed mapping instructions

### Grid Editor Package Preferences (VSN1 Only)

Configure VSN1 behavior when TouchDesigner disconnects in Grid Editor's package preferences:

| Preference | Description | Default |
|------------|-------------|---------|
| **Turn off LCD when TouchDesigner is disconnected** | Controls screen backlight when disconnected. When enabled, LCD turns off (saves power). When disabled, LCD stays on (monitor status). | Disabled |
| **Set LEDs to red when TouchDesigner is disconnected** | Controls LED state when disconnected. When enabled, all slot LEDs turn red (visual indicator). When disabled, LEDs remain in last state. | Enabled |

> **Note**: These preferences are stored in Grid Editor and persist across sessions. Configure based on your workflow preference.

---

[← User Guide](user-guide.html) | [Advanced Guide →](advanced.html)

