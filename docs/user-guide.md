# User Guide

Complete guide to all features and customization options.

## Table of Contents

- [Parameter Slots System](#parameter-slots-system)
- [Multiple Banks](#multiple-banks)
- [Parameter Shortcuts](#parameter-shortcuts)
- [Undo/Redo Operations](#undoredo-operations)
- [Step Modes](#step-modes)
- [Parameter Pulse](#parameter-pulse)
- [UI Parameter Highlighting](#ui-parameter-highlighting)
- [Customization Parameters](#customization-parameters)
- [Visual Feedback](#visual-feedback)

## Parameter Slots System

Save parameters to MIDI buttons for instant recall without hovering.

### Assigning Slots

1. **Hover over a parameter** (or parameter group) you want to save
2. **Long-press a slot button** on your controller
3. The parameter is now stored in that slot

**ParGroup Support:**
- Hover over parameter groups (RGB, XYZ, etc.) to assign the entire group
- Groups display with `>` prefix (e.g., `>Color`)
- Rotating the knob adjusts all valid parameters simultaneously
- Parameters with expressions/exports are automatically skipped

### Using Slots

- **Press a slot button** to activate that parameter
- **Adjust with encoder** without hovering
- **Press empty slot** to return to hover mode

### Clearing Slots

**Long-press any slot button while not hovering** over any parameter to clear that slot

### Jump to Operator

**Hold knob push button + press slot button** to jump to that parameter's operator in the network

### Slot States

- **Dark LED**: Slot is empty
- **Dim LED**: Slot has parameter assigned but not active
- **Bright LED**: Slot is currently active

## Multiple Banks

Organize slots into multiple banks for expanded control.

### Bank Organization

- Each bank has its own set of slots (e.g., 8 slots per bank)
- Banks are independent with separate assignments
- Each bank remembers its last active slot
- Example: Bank 0 = lighting, Bank 1 = audio, Bank 2 = video

### Using Banks

1. **Press a bank button** to switch banks
2. Slot assignments instantly change to that bank's parameters
3. Active slot is automatically recalled for that bank
4. Bank number displayed on VSN1 screen and UI

### Configuring Banks

- **Add/remove banks**: Use the `Banks` sequence parameter +/- buttons
- **Map buttons**: 
  - Manually set MIDI indices in Banks sequence, OR
  - Use Learn Mode: Hover over Index parameter and press MIDI button
  - VSN1 preset: `Use Defaults for VSN1` auto-configures

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

### Features

- **History Tracking**: Complete history of all actions
- **Cross-Parameter**: Undo changes to any parameter
- **Bank-Aware**: Works seamlessly across bank switches
- **Smart Validation**: Checks parameters still exist before restoring

> Controlled by `Enable Undo` parameter (see [Customization](#customization-parameters))

## Step Modes

Two calculation modes determine how parameter adjustments scale.

### Fixed Mode (Default)

- Uses configured step size directly (e.g., 0.001, 0.01, 0.1, 1)
- Same increment regardless of parameter range
- Best for consistent, predictable adjustments
- Example: 0.001 step always increments by 0.001

### Adaptive Mode

- Step automatically scales to parameter's min/max range
- Larger ranges = larger steps, smaller ranges = smaller steps
- Best for parameters with varying ranges
- Example: 0.001 step on 0-1 range = 0.001, but on 0-1000 range = 1

### Switching Modes

- **Via Parameter**: Set `Step Mode` custom parameter
- **Via Shortcut**: Press leftmost + rightmost step buttons simultaneously
- **Visual Feedback**: VSN1 shows "_FIXED_" or "_ADAPT_" and circle outline changes color

## Push Step Mode

Configure knob push button for alternate precision.

### Modes

**Fixed** (default):
- Hold push + rotate = uses alternate step size
- Set via `Push Step` custom parameter
- Quick assign: Hold push + press step button to set that step as alternate

**Finer**:
- Hold push + rotate = current step ÷ 10
- Gradually increase precision

**Coarser**:
- Hold push + rotate = current step × 10
- Gradually decrease precision

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
- Parameter name and value in circle indicator
- All slot names always visible (active slot highlighted)
- Default value notch on circle
- Screen outline colors:
  - Color outline = hover mode
  - White outline = slot mode
- Bank indicator (e.g., "Bank 0")
- Step size display when changed

**Knob LEDs:**
- Value-based gradual fill or step-based indicators (configurable)

### TouchDesigner UI Feedback

- Hovered parameters color-highlighted
- Editable parameters with distinct colors
- Bank indicator in UI
- Real-time updates during interaction

---

[← Getting Started](getting-started.md) | [Advanced →](advanced.md)

