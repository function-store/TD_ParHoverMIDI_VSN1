---
layout: default
title: User Guide
nav_order: 2
---

# User Guide

Complete guide to all features and customization options.

> **New to this component?** Start with [Getting Started](getting-started.html) to install and configure everything first.

## Overview

This component transforms how you control TouchDesigner parameters by combining mouse hover detection with MIDI encoders. Beyond basic hover control, you get:

- **Precision Control**: Multiple step sizes with Fixed or Adaptive modes
- **Slots & Banks**: Save parameters to buttons for instant recall across multiple banks
- **Shortcuts**: Quick button combos for reset, default, clamp operations
- **ParGroups**: Control entire parameter groups (RGB, XYZ) simultaneously  
- **Undo/Redo**: Full undo support for all operations
- **Auto-Recovery**: Automatic fixing when operators are moved/renamed

## Table of Contents

- [Step Modes](#step-modes)
- [Parameter Slots System](#parameter-slots-system)
- [Multiple Banks](#multiple-banks)
- [Parameter Shortcuts](#parameter-shortcuts)
- [Undo/Redo Operations](#undoredo-operations)
- [Parameter Pulse](#parameter-pulse)
- [UI Parameter Highlighting](#ui-parameter-highlighting)
- [Hover Timeout](#hover-timeout)
- [Customization Parameters](#customization-parameters)
- [Visual Feedback](#visual-feedback)

> **💡 Tip**: This guide focuses on features and usage. For installation and setup, see [Getting Started](getting-started.md).

---

## Step Modes

Control how precisely you adjust parameters with multiple step sizes and modes.

> **VSN1 Users**: Step buttons are the small dark buttons located under the LCD screen.

### Adjusting Precision

Use your mapped step buttons to cycle through step sizes:
- **Default steps**: 0.001, 0.01, 0.1, 1
- **Configurable** in the component's **Mapping** tab
- Current step size is displayed on the VSN1 screen

### Step Mode: Fixed vs Adaptive

Two calculation modes determine how parameter adjustments scale:

**Fixed Mode** (default):
- Uses exact configured step size (e.g., 0.01 = 0.01 increment)
- Same increment regardless of parameter range
- Best for consistent, predictable adjustments
- Example: 0.001 step always increments by exactly 0.001

**Adaptive Mode**:
- Step automatically scales to parameter's min/max range
- Larger ranges = larger steps, smaller ranges = smaller steps  
- Best for parameters with varying ranges
- Example: 0.001 step on 0-1 range = 0.001, but on 0-1000 range = 1

**Switching Modes:**
- **Via Parameter**: Set `Step Mode` custom parameter to "Fixed" or "Adaptive"
- **Via Shortcut**: Press leftmost + rightmost step buttons simultaneously
- **Visual Feedback**: VSN1 shows "_FIXED_" or "_ADAPT_" and bar outline changes color (white = Fixed, colored = Adaptive)

### Push Step Mode

Hold the knob push button while rotating for alternate precision control:

**Fixed** (default):
- Hold push + rotate = uses alternate step size
- Set via `Push Step` custom parameter
- **Quick assign**: Hold push button + press any step button to set that step as the alternate

**Finer**:
- Hold push + rotate = current step ÷ 10
- Gradually increase precision as needed

**Coarser**:
- Hold push + rotate = current step × 10
- Gradually decrease precision for faster adjustments

---

## Parameter Slots System

Save parameters to MIDI buttons for instant recall without hovering. Slots work in "sticky mode" - once activated, hovering over other parameters has no effect until you return to hover mode.

> **VSN1 Users**: Slot buttons are the 8 clicky keyboard buttons on your device.

### Assigning Slots

1. **Hover over a parameter** (or parameter group) you want to save
2. **Long-press a slot button** on your controller
3. The parameter is now stored in that slot for instant recall

### Using Slots

- **Press a slot button** to activate that parameter (enters sticky mode)
- **Adjust with encoder** without needing to hover over the parameter
- **Press an empty slot button** to return to hover mode
- **Hold knob push + press slot** to jump to that parameter's operator in the network

### Managing Slots

**Clear a slot:**
- While NOT hovering over any parameter, long-press the slot button you want to clear

**Reassign a slot:**
- With a slot active, hover over a different parameter and long-press the same slot button

### Slot States (Visual Feedback)

- **Dark LED**: Slot is empty and available for assignment
- **Dim LED**: Slot has parameter assigned but not currently active
- **Bright LED**: Slot is currently active and controlling this parameter

### ParGroup Support

Assign entire parameter groups (like RGB, XYZ) to slots for simultaneous control:

- **Hover over parameter groups** (RGB, XYZ, etc.) to assign the entire group
- **Groups display with `>` prefix** (e.g., `>Color`) to distinguish from single parameters
- **Rotating the knob** adjusts all valid parameters in the group simultaneously
- **Parameters with expressions/exports** are automatically skipped during manipulation
- **Single-parameter groups** are treated as individual parameters (no `>` prefix)

### Jump to Operator

**Hold knob push button + press slot button** to jump to that parameter's operator in the network

> Parameter slots and their assignments are saved with your project file.

---

## Multiple Banks

Organize your parameter slots into multiple banks to dramatically expand your control capabilities. Each bank is completely independent with its own set of slot assignments.

> **VSN1 Users**: Long-press any Step button (small dark buttons under the LCD) to switch banks.

### How Banks Work

- **Independent Storage**: Each bank has its own set of slots (e.g., 8 slots per bank)
- **Separate Assignments**: Banks remember their own parameter-to-slot mappings
- **Active Slot Memory**: Each bank remembers which slot was last active
- **Instant Switching**: Switch banks and immediately access different parameter sets

### Switching Banks

1. **Long-press a Step button** to switch to that bank
2. Slot assignments and labels instantly update to show that bank's parameters
3. If you had an active slot in this bank, it automatically becomes active again
4. Bank number displayed on VSN1 screen and in UI

---

## Parameter Shortcuts

Quick button combinations for common operations (works with step or bank buttons):

### Button Combinations

| Buttons | Action |
|---------|--------|
| **First + Second** | Reset to default value |
| **First + Third** | Set current value as default |
| **Second + Third** | Set current value as min (normMin and min) |
| **Second + Fourth** | Set current value as max (normMax and max) |
| **Third + Fourth** | Clamp value to min/max range |
| **First + Fourth (long press)** | Open component editor for active parameter |

### Usage Notes

- Press and hold combinations while hovering or controlling parameters
- Min/max affects both visual slider and actual parameter bounds
- Clamping brings values within defined range
- Component editor shortcut works with all parameter types

## Undo/Redo Operations

Full undo/redo support for parameter changes and slot management.

### What's Tracked

- All parameter value changes via MIDI
- Parameter resets and shortcuts
- Slot assignments
- Slot clearing
- Works across banks and parameters

### Key Features

- **History Tracking**: Complete history of all actions through the component
- **Cross-Parameter**: Undo changes to any parameter you've adjusted
- **Bank-Aware**: Works seamlessly across bank switches
- **Smart Validation**: Checks parameters still exist before restoring values

> Controlled by `Enable Undo` parameter (see [Customization](#customization-parameters))

---

## Parameter Pulse

Trigger actions on special parameter types using the Pulse button.

**Parameter Types:**
- **Pulse parameters**: Triggers pulse action
- **Momentary parameters**: Can be held for momentary trigger
- **Toggle parameters**: Toggles on/off
- **Other types**: No action

## UI Parameter Highlighting

Visual feedback in TouchDesigner interface.

### Global UI Color System

- **Hover Mode**: Parameter UI elements shift color to indicate hover mode active
- **Slot Mode**: UI colors reset to normal (slot controlling parameter)
- **Mode Transitions**: Instant color changes when switching modes

> **Note**: Can cause performance impact when switching modes. Toggle via `Enable UI Color` parameter.

### Parameter Color Coding

- **Hovered Parameters**: Highlighted in distinct color
- **UI Mirroring**: Shows hardware states directly in TD interface

### Component UI Button

Convenient button in top-right corner of TD's UI:

- **Left Click**: Opens component parameters dialog
- **Right Click**: Opens component UI view
- **Middle Click**: Toggles UI coloring on/off

---

## Hover Timeout

Control how long parameters remain active **after you stop hovering** over them.

> **While Hovering**: Parameters stay active indefinitely. You can adjust them freely with MIDI controls. Timeout and sticky settings have no effect while your cursor is over a parameter.

### Timeout Length

Set `Hover Timeout Length` parameter (in seconds) to control what happens **after you move your cursor away**:

- **Greater than 0**: Parameter stays active for the specified duration, then clears
- **Set to 0**: Parameter clears immediately when you unhover

After the timeout expires, the component returns to showing the `_HOVER_` message.

### Sticky Parameter

The `Sticky Par` toggle only matters **after you've moved your cursor away**. It controls whether MIDI adjustments extend the timeout:

**Enabled**:
- You move cursor away → timeout countdown starts
- You adjust with MIDI → countdown restarts (parameter stays active longer)
- You stop adjusting → parameter clears after timeout duration
- Result: Parameter stays active as long as you're adjusting it
- **Bonus**: Hovering over invalid parameters (unsupported types, read-only, etc.) is ignored - keeps your valid parameter active. Expression parameters still show.

**Disabled**:
- You move cursor away → timeout countdown starts
- You adjust with MIDI → countdown continues unchanged
- Parameter clears after the original timeout, even if you're still adjusting
- Result: Parameter has a fixed lifetime from when you unhover

**Summary:**
- **While hovering**: Parameters stay active indefinitely, regardless of settings
- **After unhovering**: Timeout and sticky settings determine how long the parameter remains active
- **In slot mode**: Parameters stay active until you deactivate the slot (timeout doesn't apply)
- **With sticky enabled**: Invalid parameters (except expressions) are ignored, preventing accidental interruption of your workflow

---

## Customization Parameters

All available parameters for customizing behavior:

### Step Configuration

- **`Step Size`**: Adjustable in each Step block (default: 0.001, 0.01, 0.1, 1)
- **`Step Mode`**: "Fixed" or "Adaptive" (toggle: leftmost + rightmost step buttons)
- **`Push Step Mode`**: "Fixed", "Finer", or "Coarser"

### Parameter Behavior

- **`Loop Menus`**: When enabled, menu parameters loop (last → first). When disabled, stops at edges.
- **`Control StrMenus`**: Allow control of StrMenu parameters (both `isMenu` and `isString`). Note: StrMenus assigned to slots remain controllable even when disabled.

### Undo System

- **`Enable Undo`**: Enable/disable undo/redo for all operations
- **`Undo Timeout (ValueChange)`**: Seconds to wait before pushing value changes to undo stack (groups rapid adjustments). Default: 1 second.

### VSN1 Integration

- **`VSN1 Support`**: Enable screen updates and LED feedback (requires Grid Editor open)
- **`Label Display Mode`**: "Compressed" (removes vowels/spaces) or "Truncated" (simple cut-off)
- **`Knob LED Update`**: "Off", "Value", or "Step" for knob ring LED indication
- **`Reset Comm`**: Pulse to reset websocket connection if Grid Editor reports issues

### UI Settings

- **`Enable UI Color`**: Apply color highlighting to TD interface (performance impact when switching modes)
- **`Enable UI`**: Toggle internal UI that mirrors VSN1 state (disabling saves ~50% performance)

## Visual Feedback

Comprehensive feedback through hardware and software.

### VSN1 Hardware Feedback

**Button LEDs:**
- Dark: Slot empty (hover mode)
- Dim: Slot assigned but not active
- Bright: Slot currently active

**Screen Display:**
- Parameter name and value
- All slot names always visible (active slot highlighted)
- Default value notch on circle
- Screen outline colors:
  - Color outline = hover mode
  - White outline = slot mode
- Bank indicator (e.g., "Bank 0")
- Step size display when changed and indicated

**Knob LEDs:**
- Value-based gradual fill or step-based indicators (configurable)

### TouchDesigner UI Feedback

- Hovered parameters color-highlighted
- Editable parameters with distinct colors
- Bank indicator in UI
- Real-time updates during interaction

---

[← Getting Started](getting-started.html) | [Advanced →](advanced.html)

