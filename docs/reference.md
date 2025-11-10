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

- [Quick Reference](#quick-reference)
  - [Table of Contents](#table-of-contents)
  - [Controls \& Shortcuts](#controls--shortcuts)
  - [All Parameters](#all-parameters)
  - [VSN1 MIDI Mappings](#vsn1-midi-mappings)
    - [MIDI Configuration Notes](#midi-configuration-notes)
    - [Custom MIDI Controllers](#custom-midi-controllers)
    - [Grid Editor Package Preferences (VSN1 Only)](#grid-editor-package-preferences-vsn1-only)

---

## Controls & Shortcuts

Complete reference for all hardware controls and keyboard shortcuts.

> **📖 Hardware Glossary (VSN1)**:
> - **Slot Buttons** - The 8 clicky keyboard buttons on the device (with LED feedback)
> - **Step Buttons** - The 4 small dark buttons located under the LCD screen
> - **Bank Button** - Any step button when long-pressed (switches banks)
> - **Main Knob** - The rotary encoder (twist to adjust, push to pulse/toggle)

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
| First + third button | Set current as default | Custom parameters only |
| Second + third button | Set current as min | Custom parameters only |
| Second + fourth button | Set current as max | Custom parameters only |
| Third + fourth button | Clamp to range | Custom parameters only |
| First + fourth (long-press) | Open component editor | Opens active parameter's operator, or selected COMP if none |
| **Network Zoom** (when enabled & no active parameter) | | |
| Twist knob clockwise | Zoom in + pan to cursor | Seek or Target mode (configurable) |
| Twist knob counter-clockwise | Zoom out + pan | Works until zoom limit (3x) |
| Push knob + twist | Zoom in fast | Larger zoom increment per twist |
| Double-click knob push button | Home network editor | Fit all to view |

> **Button References**: "First" = leftmost, "Second" = second from left, etc. On VSN1: step buttons are under LCD, slot buttons are the 8 clicky keyboard buttons.

---

## All Parameters

Complete parameter reference organized by TouchDesigner parameter page.

| Parameter | Description | Default |
|-----------|-------------|---------|
| **📄 Custom Page** | | |
| `Active` | Enable/disable entire component | On |
| `MIDI Status` | Shows MIDI connection state (read-only) | - |
| `Connected Status` | Shows websocket connection state (read-only) | - |
| `Re-Init` | Pulse to reinitialize component | - |
| `Step Mode` | "Fixed" or "Adaptive" precision | Fixed |
| `Push Step Mode` | "Fixed", "Finer", or "Coarser" | Coarser |
| `Push Step` | Current push step value (read-only) | 0.01 |
| `Loop Menus` | Menu parameters wrap around | On |
| `Control StrMenus` | Allow string-menu parameter control | On |
| _Shortcuts_ | _(Section header)_ | |
| `Shortcuts` | Enable button combo shortcuts | On |
| `Slot Learn Hold Length` | Long-press duration for slot assignment (sec) | 0.33 |
| `Bank Switch Hold Length` | Long-press duration for bank switching (sec) | 0.34 |
| `Reset Par Hold Length` | Long-press duration for parameter reset (sec) | 0.01 |
| `MinMaxClamp Hold Length` | Long-press duration for clamp operations (sec) | 0.01 |
| `Customize Hold Length` | Long-press for component editor jump (sec) | 0.33 |
| _Misc_ | _(Section header)_ | |
| `Hover Timeout Length` | Seconds parameter stays active after unhover | 0.33 |
| `Sticky Par in Timeout` | MIDI adjustments restart timeout countdown | On |
| `Enable Undo` | Enable undo/redo functionality | On |
| `Undo Timeout (ValueChange)` | Delay before pushing value changes to stack (sec) | 1 |
| `Slots Repo` | Reference to external storage table | ./SlotsRepo |
| `Auto Create Repo` | Automatically create external repo on init | On |
| `Create` | Pulse to manually create external repo | - |
| **📄 VSN1 / UI Page** | | |
| _Intech Studio VSN1 Support_ | _(Section header)_ | |
| `VSN1 Support` | Enable VSN1 screen/LED feedback | On |
| `Start Grid Editor` | Pulse to launch Grid Editor | - |
| `Auto-start Grid Editor` | Launch Grid Editor on TD startup | On |
| `Network Address` | Websocket address | 127.0.0.1 |
| `Port` | Websocket port | 9642 |
| `Periodic Reconnect` | Attempt periodic reconnection | On |
| `Reconnect Period` | Reconnection interval (sec) | 5 |
| `Reset Comm` | Pulse to reset websocket connection | - |
| `Knob Led Update` | LED mode: "Off", "Value", or "Step" | Value |
| _TD UI_ | _(Section header)_ | |
| `Enable UI` | Enable internal UI display | On |
| `Hide Author Label` | Hide author name from UI | Off |
| `UI Post FX` | Enable bloom effect on UI | Off |
| `Color Hovered UI` | Apply color to hovered UI elements | On |
| `Activate Slot on Jump` | Activate parameter when jumping to operator | On |
| `Use Current Zoom for Jump` | Maintain current zoom level on jump | Off |
| `Enable Knob Zoom (if no Par)` | Enable network editor zoom navigation | On |
| `Zoom Mode` | "Seek" (follow cursor) or "Target" (lock) | Seek |
| `Zoom Network` | Zoom speed per knob increment | 0.015 |
| `Zoom Interpolation` | Camera movement smoothness (0.0-1.0) | 0.015 |
| _General UI Settings_ | _(Section header)_ | |
| `Color Index` | Color palette index for UI | 1 |
| `Label Display Mode` | "Compressed" or "Truncated" | Compressed |
| **📄 Mapping Page** | | |
| `Device Id` | MIDI device identifier | 1 |
| `Channel` | MIDI channel | 16 |
| `Learn` | Enter MIDI learn mode | - |
| `Clear` | Clear learned MIDI mappings | - |
| `Use Defaults for VSN1` | Load default VSN1 MIDI mappings | - |
| `Knob Index` | MIDI CC index for main knob | 9 |
| `Push Index` | MIDI CC index for knob push button | 9 |
| _Steps_ | _(Section header)_ | |
| `Index` | MIDI index for step buttons | 13 |
| `Step` | Step size value | 1.0 |
| _Slots_ | _(Section header)_ | |
| `Index` | MIDI index for slot buttons | 8 |
| _Banks_ | _(Section header)_ | |
| `Index` | MIDI index for bank buttons | 13 |
| **📄 About Page** | | |
| `Author` | Component author (read-only) | Function Store |
| `Author Links` | Open author website | - |
| `README` | Open documentation site | - |
| `CHEATSHEET` | Open HTML cheatsheet in browser | - |
| `Version` | Current version (read-only) | - |
| `Check` | Check for updates | - |
| `Update` | Download and install update | - |
| `Externalize Component` | Save to palette and externalize repo | - |
| `Show Builtin Params` | Show built-in TD parameter pages | Off |

> **💡 Parameter Help**: Hover over any custom parameter in the component while holding **Alt** (or **Option** on Mac) to see detailed help text.

---

## VSN1 MIDI Mappings

Default MIDI CC mappings for Intech Studio VSN1 hardware.

| Control | MIDI CC | Type | Notes |
|---------|---------|------|-------|
| **Encoders** | | | |
| Main Knob (twist) | 9 | Relative | Endless encoder, sends relative values |
| Main Knob (push) | 9 | Momentary | Button press on knob |
| **Step Buttons** (under LCD) | | | |
| Step 0 (0.001) | 10 | Toggle | Also used for bank 0 switching (long-press) |
| Step 1 (0.01) | 11 | Toggle | Also used for bank 1 switching (long-press) |
| Step 2 (0.1) | 12 | Toggle | Also used for bank 2 switching (long-press) |
| Step 3 (1.0) | 13 | Toggle | Also used for bank 3 switching (long-press) |
| **Slot Buttons** (clicky keyboard) | | | |
| Slot 0 | 1 | Toggle | With LED feedback |
| Slot 1 | 2 | Toggle | With LED feedback |
| Slot 2 | 3 | Toggle | With LED feedback |
| Slot 3 | 4 | Toggle | With LED feedback |
| Slot 4 | 5 | Toggle | With LED feedback |
| Slot 5 | 6 | Toggle | With LED feedback |
| Slot 6 | 7 | Toggle | With LED feedback |
| Slot 7 | 8 | Toggle | With LED feedback |

### MIDI Configuration Notes

- **Device ID**: Default is `1`, match this with TouchDesigner's MIDI Device Mapper
- **Channel**: Default is `16`
- **Relative Encoding**: Knob uses relative/endless encoding (not absolute 0-127)
- **LED Feedback**: Slot buttons receive LED state updates via MIDI
- **Screen Updates**: VSN1 screen controlled via websocket (port 9642), not MIDI

> **⚠️ Indexing Note**: TouchDesigner uses 1-based indexing for Channel and MIDI CC, while Grid Editor uses 0-based indexing. For example, Channel 16 in TD = Channel 15 in Grid Editor. This is important for custom/manual mappings.

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

