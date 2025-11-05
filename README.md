# TouchDesigner Par Hover Control for VSN1

A [TouchDesigner](https://derivative.ca) component designed for the **[Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r)** that provides intuitive parameter control using **endless relative MIDI encoders** and mouse hover interactions. While optimized for VSN1, it's compatible with other endless relative MIDI controllers. **Standard potentiometers will not function as intended.**

## Overview

This component enables seamless parameter adjustment in TouchDesigner by combining mouse hover detection with VSN1's endless encoders and visual feedback system. Simply hover your mouse over any parameter and use the VSN1's knob to make precise adjustments without clicking or dragging. The VSN1's screen and LEDs provide real-time feedback, while the system controls one parameter at a time based on your mouse hover position.

> Relative MIDI means the device sends a value less or greater than 64 to indicate movement in either direction. The greater the difference, the bigger the movement. The sensitivity is configurable for VSN1 for example.

> This repo also contains the [Grid Editor](https://intech.studio/products/editor) package that needs to be added to the editor, see [Installation Steps](#installation)

Below is a summary of the features mapped to [Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r), the target hardware of this repo.

![](https://github.com/function-store/TD_ParHoverMIDI_VSN1/blob/main/docs/images/hoveredvsn1.jpg)

## Features

- **VSN1-Optimized Control**: Designed specifically for VSN1's endless encoders and visual feedback system
- **Hover-based Parameter Control**: Adjust any parameter by hovering your mouse over it
- **UI Parameter Highlighting**: Visual feedback in TouchDesigner UI - hovered parameters are highlighted in color, and editable parameters (those that can be adjusted) are shown in a distinct color
- **ParGroup Support**: Hover over and control entire parameter groups (like RGB, XYZ) simultaneously - manipulates all valid parameters in the group at once
- **Multiple Parameter Slots**: Assign parameters or parameter groups to VSN1 buttons for instant access and switching
- **Multiple Banks**: Organize slots into separate banks using VSN1 buttons for expanded parameter control
- **Smart Learning System**: Automatically assign VSN1 button mapping
- **Enhanced Parameter Support**: Full support for Numeric, Menu, Toggle, and Pulse parameters
- **Adjustable Precision**: Change adjustment step sizes using VSN1 step buttons
- **Step Mode**: Choose between Fixed (fixed step size) or Adaptive (step scales with parameter range)
- **Push Step Mode**: Knob push button with three modes - Fixed (hold and rotate for alternate step), Finer (hold for next smaller step), or Coarser (hold for next larger step)
- **Parameter Value Shortcuts**: Multiple button combinations for quick operations (reset, set default, set min/max, clamp values)
- **Quick Parameter Customization**: Long-press first and last step/bank buttons to instantly open the component editor for any active custom parameter
- **Value Undo/Redo**: Full undo/redo support for parameter value adjustments using standard keyboard shortcuts (Ctrl+Z/Ctrl+Y on Windows, Cmd+Z/Cmd+Shift+Z on Mac)
- **Real-time VSN1 Feedback**: Full integration with VSN1's built-in screen and LED system
  - **LED Feedback**: Color-coded LEDs showing slot states (dark/dim/bright)
  - **Enhanced Screen Display**: Always-visible slot names, parameter values with default value notch, bank indicators
  - **Visual State Indicators**: Screen outline colors indicate current mode (hover/slot active)
- **Generic MIDI Compatibility**: Also works with other endless/relative MIDI encoders (without visual feedback)

## Hardware Compatibility

### Primary Target Hardware
- **Intech Studio VSN1**: Full native support with optimized mappings, screen updates, and LED feedback

### Alternative Hardware (Limited Support)
- **Generic MIDI Controllers**: Compatible with endless encoders in relative mode (no visual feedback)
- **MIDI Button Controllers**: For step size and bank adjustment functionality
> Turn off `VSN1 Support` custom parameter in the TouchDesigner component to avoid issues.

### Requirements
- TouchDesigner (2023.12120+)
- **Intech Studio VSN1** (recommended) or other endless relative MIDI encoder
- USB connection to VSN1 or MIDI interface for other controllers
- **For full VSN1 integration**: Grid Editor must be open with exclusive access to port `9642`

## Installation

### Intech Studio Grid Editor

**Install the Grid Package:**
1. Clone the repository
2. Run `npm i` in the root folder
3. Run `npm run build` to build the necessary files
4. In the Editor at the Package Manager panel, either Approve the package at the top of the list if possible or use the `+ Add external package` button to add the **root** path of the package (for example, `C:\Users\...\TD_ParHoverMIDI_VSN1`)

> If updating, it is recommended to also grab the new .tox file release!

**Import the VSN1 Configuration:**
1. On your VSN1 device, look for, and import `TouchDesigner Par Hover Control` from the Grid Editor 
2. Keep Grid Editor open at all times when using VSN1 (exclusive access to port `9642` required)

> For mapping configuration details, see [MIDI Mapping Configuration](#midi-mapping-configuration)

### TouchDesigner

1. Connect your MIDI controller to your system
2. Configure MIDI settings in TouchDesigner (Dialogs -> MIDI Mapper)
3. Download `ParHoverMIDI_VSN1.tox` from the [latest release](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest)
4. Drag `ParHoverMIDI_VSN1.tox` into your TouchDesigner project (suggested `/` root)
5. **Set your `Device ID`** in the component's **Mapping** tab (find your device ID in TouchDesigner's MIDI Device Mapper)
6. Have Grid Editor open at all times when using Intech hardware (see next section)

## Quick Start
0. Download `ParHoverMIDI_VSN1.tox` from the [latest release](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest)
1. **Setup**: Place the `ParHoverMIDI_VSN1.tox` component in your network (suggested at root `/`)
2. **MIDI Configuration**: Ensure your MIDI device is recognized in TouchDesigner's Device Manager
3. **⚠️ Set Device ID**: Open the component's **Mapping** tab and set your `Device ID` (find it in TouchDesigner's MIDI Device Mapper)
4. (Optional) **MIDI Mapping**: Configure your MIDI mappings - see [MIDI Mapping Configuration](#midi-mapping-configuration)
   - **VSN1 users**: Pulse `Use Defaults for VSN1` to automatically configure everything
   - **Other controllers**: Use manual mapping or Learn Mode
5. **Usage**: Hover over any parameter and twist your MIDI controller to adjust that specific parameter's value
6. **Step Sizes**: Use assigned MIDI buttons to cycle through different step sizes for fine/coarse control
    - Configure step sizes in the **Mapping** tab (default: 0.001, 0.01, 0.1, 1)
7. **Parameter Slots**: Check [Parameter Slots System](#parameter-slots-system) to save and recall parameters to control!
8. **Multiple Banks**: Use [Multiple Banks](#multiple-banks) to organize slots into separate banks for expanded control

## MIDI Mapping Configuration

### Default VSN1 Mapping
For VSN1 users, the `Use Defaults for VSN1` button automatically configures all MIDI mappings according to the Grid Editor package defaults:
- **MIDI Channel**: 16 (appears as **15** in Grid Editor interface)
- **MIDI Indices**: Correspond to **element indices** in the grid configuration (**1-indexed** in TouchDesigner, **0-indexed** in Grid Editor)

### Manual Mapping
For custom configurations or non-VSN1 users wanting to adapt to their devices:

**In TouchDesigner:**
- **⚠️ CRITICAL**: Set your `Device ID` in the component's **Mapping** tab parameters
  - Find your device ID in TouchDesigner's MIDI Device Mapper (Dialogs -> MIDI Mapper)
  - This must match your physical MIDI controller
- Set MIDI `Channel` in the component's **Mapping** tab parameters (default: 16 for VSN1)
- Map MIDI indices manually using the custom parameters in the **Mapping** tab
- Use **Learn Mode**: Hover over empty mapping fields and move your MIDI knobs/buttons to automatically assign them
- Configure step sizes in the **Mapping** tab (default: 0.001, 0.01, 0.1, 1)

**In Grid Editor (VSN1):**
- The **System** element defines the channel as global variable `gch`
- Each element's MIDI block can be customized if needed


## Functions


### Parameter Slots System
The component supports multiple parameter slots that can be assigned to different MIDI buttons for quick access:

**Slot Assignment**:
- **Hover over a parameter** you want to assign to a slot
- **Hover over a parameter group** (ParGroup) to assign the entire group to a slot
- **Long-press a slot button** (configured in the Slots sequence) to assign the hovered parameter/group to that slot
- **The parameter or group is now "stored"** in that slot for quick access
- **Clear a slot**: Long-press any slot button while not hovering over any parameter to free up that slot (and return it to **normal hover mode**)

**Slot Activation**:
- **Press any assigned slot button** to activate that parameter or group slot
- **The stored parameter/group becomes active** for adjustment without needing to hover
- **VSN1 screen updates** to show the active slot parameter (for groups, displays first parameter's value)
- **VSN1 LED feedback**: The active slot button lights up, previous slot LED turns off automatically

**Jump to Operator**:
- **Hold the knob push button and press any active slot button** to jump to the parameter's owner operator in the network
- **Network navigation**: The network view centers on and selects the operator containing the slot's parameter
- **Use Case**: Quickly locate and inspect operators without manually searching through your network

**Return to Hover Mode**:
- **Press an empty slot button** (one without an assigned parameter) to return to normal hover mode
- **All VSN1 slot LEDs turn off** when returning to hover mode

**ParGroup Support**:
- **ParGroups** (like RGB color, XYZ position) are fully supported and can be assigned to slots
- **Visual indicator**: ParGroup labels display with a `>` prefix (e.g., `>Color`) to distinguish them from single parameters
- **Simultaneous control**: Rotating the knob adjusts all valid parameters in the group at once
- **Smart handling**: Parameters with expressions or exports are automatically skipped during manipulation
- **Single-parameter groups**: If a ParGroup contains only 1 parameter, it's treated as a single parameter (no `>` prefix)

> Parameter slots and ParGroups are saved with the project file / component.

### Multiple Banks
The component supports multiple banks to organize your parameter slots, dramatically expanding your control capabilities:

**Bank Organization**:
- **Each bank** contains its own set of parameter slots (e.g., 8 slots per bank)
- **Banks are independent** - each bank remembers its own slot assignments and active slot
- **Bank switching** instantly loads a different set of parameter assignments
- **Example**: Bank 0 might control lighting parameters, Bank 1 audio effects, Bank 2 video parameters

**Bank Configuration**:
- **Add banks**: Use the `Banks` sequence parameter +/- buttons to add/remove banks
- **Manual mapping**: Set MIDI note indices in the Banks sequence for bank selection buttons
- **Learning mode**: Hover over a Banks sequence Index parameter and press your desired MIDI button
- **VSN1 preset**: The `Use Defaults for VSN1` parameter automatically configures bank buttons

**Bank Switching**:
- **Press a bank button** to switch to that bank
- **Slot assignments change** - button labels and colors update to show the new bank's slots
- **Active slot recalled** - if you had an active slot in this bank, it becomes active again
- **Bank indicator** - both VSN1 screen and UI show the current bank number
- **Independent operation** - each bank operates exactly like the original single-bank system

**Bank Memory**:
- **Last active slot** - each bank remembers which slot was last active
- **Slot assignments** - each bank maintains its own parameter-to-slot mappings
- **Seamless switching** - return to any bank and continue where you left off

**Visual Feedback**:
- **Bank indicator** - current bank number displayed on VSN1 screen and UI
- **Button labels** - slot button labels update to show parameters from current bank
- **Button colors** - slot button colors reflect the current bank's slot states (empty/occupied/active)
- **VSN1 LEDs** - slot LEDs update to match current bank's assignments

> Banks and their slot assignments are saved with the project file / component.

### Step Mode (`Step Mode`)
The component supports two different step calculation modes that determine how parameter adjustments are scaled:

**Fixed Mode**:
- **Fixed step size**: Uses the configured step size value directly (e.g., 0.001, 0.01, 0.1, 1)
- **Consistent behavior**: Same step increment regardless of parameter range
- **Best for**: Parameters where you want consistent, predictable step sizes
- **Example**: A parameter with range 0-1 using step 0.001 will increment by exactly 0.001

**Adaptive Mode**:
- **Adaptive step size**: Step size automatically scales based on the parameter's min/max range
- **Range-aware**: Larger parameter ranges result in larger steps, smaller ranges result in smaller steps
- **Best for**: Working with parameters of varying ranges while maintaining proportional control
- **Example**: Step 0.001 on a 0-1 range increments by 0.001, but on a 0-1000 range increments by 1

**Switching Modes**:
- **Via Parameter**: Set the `Step Mode` custom parameter to "Fixed" or "Adaptive"
- **Via VSN1 Shortcut**: Press the leftmost and the rightmost step buttons simultaneously to toggle between modes
- **Visual Feedback**: VSN1 screen briefly displays "_FIXED_" or "_ADAPT_" when mode changes, and the circle's outline color switches between white (Fixed) and colored (Adaptive)

### Push Step Mode (`Push Step Mode`)
The knob push button functionality can be configured for different step size behaviors when rotating while pushed:

**Fixed Mode**:
- **Hold the knob push button and rotate**: While hovering over or controlling any parameter
- **Result**: Uses a fixed alternate step size for finer or coarser control settable by the `Push Step` custom parameter
- **Quick Step Assignment**: While holding the knob push button, press any step button to set that step size as the alternate step
- **Use Case**: Quickly switch between two specific precision levels without cycling through step buttons

**Finer Mode**:
- **Hold the knob push button and rotate**: While hovering over or controlling any parameter
- **Result**: Uses the current primary step size divided by 10.
- **Use Case**: Gradually increase precision as needed without manual step selection

**Larger Mode**:
- **Hold the knob push button and rotate**: While hovering over or controlling any parameter
- **Result**: Uses the current primary step size multiplied by 10.
- **Use Case**: Gradually decrease precision as needed without manual step selection

### Parameter Pulse (`Pulse Index`)
- **Press this MIDI button**: While hovering over a parameter
- **For Pulse parameters**: Triggers the pulse action
- **For Momentary parameters**: Can be held for momentary trigger
- **For Toggle parameters**: Toggles the parameter on/off
- **Other parameter types**: No action (returns false)

### Shortcuts
Convenient button combinations for quick parameter operations:

**Button Combinations**:
- **First + Second step/bank buttons**: Reset parameter to its default value
- **First + Third step/bank buttons**: Set current value as default (parameter will reset to this value)
- **Second + Third step/bank buttons**: Set current value as normMin and min (slider and parameter minimum)
- **Second + Fourth step/bank buttons**: Set current value as normMax and max (slider and parameter maximum)
- **Third + Fourth step/bank buttons**: Clamp current value to min/max range (brings value within bounds)
- **First + Fourth step/bank buttons (long press)**: Open the active parameter's component editor
  - If no parameter is hovered or slot is active, selecting a COMP opens that COMP's Component Editor

**Usage**:
- Press and hold the button combinations while hovering over or controlling any parameter
- These shortcuts provide quick access to common parameter operations without opening dialogs
- Setting min/max affects both the visual slider range (normMin/normMax) and the actual parameter bounds (min/max)
- Clamping ensures the value stays within the defined min/max range
- Long press first and last buttons to quickly open the component editor for deeper parameter editing
- Faster than using Secondary Mode's reset hold functionality
- **Compatibility**: Works with all numeric parameter types (component editor shortcut works with all parameter types)

### Undo/Redo Operations
Full undo/redo support for both parameter value adjustments and slot management, allowing you to experiment freely and revert changes if needed:

**Keyboard Shortcuts**:
- **Undo**: Press `Ctrl+Z` (Windows/Linux) or `Cmd+Z` (Mac) to undo the last action
- **Redo**: Press `Ctrl+Y` (Windows/Linux) or `Cmd+Shift+Z` (Mac) to redo a previously undone action

**What Gets Tracked**:
- All parameter value changes made via MIDI knob rotation
- Changes to individual parameters and ParGroups
- Parameter value adjustments across different banks and slots
- Parameter resets and value shortcuts (via Secondary Mode or button combinations)
- Slot assignments (assigning parameters to slots)
- Slot clearing (removing parameters from slots)

**Key Features**:
- **History Tracking**: Maintains a complete history of all actions made through the component
- **Cross-Parameter**: Undo/redo works across different parameters - revert changes to any parameter you've adjusted
- **Bank-Aware**: Works seamlessly across bank switches - undo changes from any bank
- **Smart Validation**: Automatically validates that parameters still exist before restoring values

**Note**: All undo/redo functionality is controlled by the `Enable Undo` parameter in the component settings. When enabled, both parameter value changes and slot assignments/clearing are tracked.

### Parameter Recovery System
Automatic detection and recovery of invalid parameters when operators are moved, renamed, or deleted:

**Automatic Detection**:
- **On slot activation**: When you try to activate a slot with an invalid parameter
- **On bank switching**: When switching to a bank containing invalid parameters
- **On parameter interaction**: When attempting to manipulate an invalid parameter
- **Background validation**: System automatically scans for invalid parameters after certain operations

**Recovery Dialog**:
When invalid parameters are detected, a recovery dialog appears with:
- **Parameter information**: Shows the original operator path and parameter name
- **Fix button**: Edit the path to point to the new location/name of the parameter
  - Batch update: Automatically updates all other slots with the same operator path
  - Smart path matching: Handles both exact matches and child operator paths
- **Clear button**: Remove only the invalid parameter from this specific slot
  - Single operation: Only affects the slot that triggered the dialog
- **Clear All button**: Remove the invalid parameter from all related slots
  - Batch clear: Automatically clears all slots with the same operator path
- **Sequential processing**: If multiple parameters are invalid, dialogs appear one at a time

**Batch Operations**:
- **Batch path updates**: When using Fix, all other slots pointing to the same operator are automatically updated
- **Single clear**: When using Clear, only the current slot is affected
- **Batch clearing**: When using Clear All, all slots with parameters from that operator are cleared at once
- **Smart recovery**: The system identifies related parameters and offers batch operations when appropriate

**Common Use Cases**:
- **Operator moved**: You moved `/project1/geo1` to `/project1/effects/geo1` → Use Fix to update all related slots
- **Operator renamed**: You renamed `circle1` to `shape1` → Use Fix to update the path for all related slots
- **Operator deleted**: You deleted an operator → Use Clear All to remove from all slots, or Clear to remove from just this slot
- **Single slot cleanup**: One slot has wrong parameter → Use Clear to remove only that slot
- **Project reorganization**: Restructured your network → Use Fix to update paths in bulk for all related slots

**Undo Support**:
- **Fix operations are undoable**: Press Ctrl+Z/Cmd+Z to revert batch path updates
- **Clear operations are undoable**: Undo single slot clears to restore the parameter
- **Clear All operations are undoable**: Undo batch clear operations to restore all cleared slots

**Visual Feedback**:
- **`_INVALID_` message**: Displays on screen when attempting to access invalid parameters
- **Dialog prompts**: Clear interface for fixing or clearing invalid parameters with granular control
- **Seamless recovery**: After fixing, operation continues normally with the corrected parameter

> The recovery system ensures your slot assignments remain valid even as your TouchDesigner network evolves, with intelligent batch operations and granular control to handle parameters exactly as needed.

### UI Parameter Highlighting
Visual feedback in the TouchDesigner UI helps identify which parameters can be controlled:

**Global UI Color System**:
The component modifies TouchDesigner's global interface colors to provide visual feedback about the current mode:
- **Hover Mode**: All parameter UI elements (buttons, sliders, numeric fields, toggles, menus) are color-shifted in the UI to indicate hover mode is active
- **Slot Mode**: The UI colors reset to normal, showing that a slot is currently controlling a parameter rather than hovering
- **Mode Transitions**: The color shift happens instantly when switching between hover and slot modes
> **NOTE**: Changing UI colors can cause some performance impact when switching between hover mode and slot mode. This feature therefore can be toggled off via custom parameter, or quick access via the **Component UI Button** (see below)

**Parameter Color Coding**:
- **Hovered Parameters**: When you hover over a parameter, it's highlighted in a distinct color in the UI
- **UI Mirroring**: The component mirrors the hardware states and makes it immediately clear which parameter is currently targeted and which parameters are controllable, etc.

**Component UI Button**:
The component includes a convenient button in the top-right corner of TD's UI for quick access:
- **Left Click**: Opens the component's parameters dialog
- **Right Click**: Opens the component's UI (user interface view)
- **Middle Click**: Toggles UI coloring on/off - enables or disables the global UI color modification feature

This comprehensive visual system provides clear feedback about parameter states directly in the TouchDesigner interface, complementing the VSN1's screen and LED feedback.

## Customization Parameters

The following parameters are available to further customize the functionality of the component:
- **`Step Size`**: Adjustable in each `Step` block.
- **`Step Mode`**: Choose between "Fixed" (fixed step size) or "Adaptive" (step scales with parameter range). Can also be toggled by pressing the leftmost and rightmost step buttons simultaneously.
- **`Push Step Mode`**: Choose between "Fixed" (uses alternate step when knob pushed), "Finer" (uses current primary step size divided by 10), or "Larger" (uses current primary step size multiplied by 10).
- **`Loop Menus`**: When enabled, menu parameters loop around (last item → first item). When disabled, menu navigation stops at the edges.
- **`Enable Undo`**: When enabled, all operations (parameter value changes, parameter resets, slot assignments, and slot clearing) can be undone/redone. Undo/redo works across banks and validates parameter existence before restoring.
- **`Undo Timeout (ValueChange)`**: Defines how long (in seconds) after a parameter value change the system waits before pushing it to the undo stack. This allows for continuous adjustments to be grouped into a single undo action, preventing excessive undo history entries during rapid knob movements. Default: 1 seconds.
- **`VSN1 Support`**: Enables VSN1 screen updates and LED feedback, displaying adjusted parameter and value (circle size between param normMin/Max values), using websocket communication --- requires Grid Editor to be open!
- **`Label Display Mode`**: Choose between "Compressed" (removes vowels/spaces) or "Truncated" (simple cut-off) for parameter label formatting on limited displays
- **`Enable UI Color`**: When enabled, applies visual color highlighting to parameters in the TouchDesigner interface to indicate hovered/active states. **NOTE**: Changing UI colors can cause some performance impact when switching between hover mode and slot mode.
- **`Reset Comm`**: In case GRID Editor reports websocket connection is not active try pulsing this.
- **`Knob LED Update`**: Choose between "Off", "Value" and "Step" to determine what is indicated on the knob LEDs of VSN1. **NOTE**: Currently when set to "Value", laggy updates can be observed on the hardware unit.

## Visual Feedback

The component provides comprehensive visual feedback through both VSN1 hardware and TouchDesigner UI:

### **VSN1 Hardware Feedback**

**Button LED States**:
- **Dark**: Slot is free and available for assignment (hover mode)
- **Dim**: Slot has a parameter assigned but is not currently active
- **Bright**: Slot is currently active and controlling this parameter

**Screen Display**:
- **Parameter Value**: Shows current parameter name and value in a circle indicator
- **Slot Names**: All slot names are always displayed on screen for quick reference
  - *The active slot name is highlighted!*
- **Default Value Notch**: A visual notch on the circle indicates the parameter's default value position
- **Screen Outline Colors**:
  - **Color outline**: Currently in hover mode - move mouse to select parameters
  - **White outline**: Currently in slot mode - a parameter slot is active
- **Bank Indicator**: Shows current bank number (e.g., "Bank 0", "Bank 1")
- **Step Size**: Displays current step value when step size changes

**Button Updates**:
- Slot button labels and LEDs update when switching banks
- Label compression intelligently fits parameter names to display

**Knob LEDs**: 
- **Knob ring LEDs** show visual feedback of value-based gradual fill or step-based indicators, depending on setting

### **TouchDesigner UI Feedback**

**Parameter Highlighting**:
- **Hovered Parameters**: Color-highlighted to indicate current mouse hover target
- **Editable Parameters**: Distinct color coding for parameters that can be adjusted
- **Bank Indicator**: Current bank number displayed in the UI
- **Real-time Updates**: Visual feedback updates instantly as you interact with parameters

This comprehensive visual system makes it immediately clear whether you're in hover mode or slot mode, which bank you're currently using, which slots are available, occupied, or active, which parameters can be controlled, and what precision level you're currently using for parameter adjustments.

## Known Issues
- Screen updates can be laggy (it is trying its best though)

## Future Plans / Roadmap

### Enhanced Slot Management
- ✅ **LED feedback for active slots**: Implemented - LEDs show which slot is currently active
- ✅ **Multiple banks**: Implemented - organize slots into separate banks for expanded control
- ✅ **Bank memory**: Implemented - each bank remembers its last active slot and assignments
- ✅ **Visual bank indicators**: Implemented - screen and UI show current bank number
- **Enhanced visual indicators**: Additional color-coded LEDs or screen indicators for different slot states


## Known Issues
- You tell me!

## Development

### Project Structure
The codebase has been refactored into a modular architecture for better maintainability:

```
scripts/HoveredMidiRelative/
├── constants.py              # All constants and enums
├── validators.py             # Parameter validation logic
├── formatters.py             # Label and value formatting utilities
├── decorators.py             # Common decorators for validation/blocking
├── handlers.py               # MIDI message processing
├── managers/
│   ├── slot_manager.py       # Parameter slot operations & invalidation
│   ├── display_manager.py    # Unified display & VSN1 hardware rendering
│   ├── ui_manager.py         # Local UI element management
│   ├── undo_manager.py       # Undo/redo system for all operations
│   └── repo_manager.py       # Persistent storage management
└── HoveredMidiRelativeExt.py # Main extension class
```

> This repo also contains the Grid package code for a monolithic repo, and is based on the [example package](https://github.com/intechstudio/package-websocket).

**Core Components:**
- **`HoveredMidiRelativeExt`**: Main extension class with TouchDesigner integration
- **`MidiMessageHandler`**: Processes MIDI input (steps, knobs, pulses, slots, banks) with ParGroup support
- **`DisplayManager`**: Centralizes all display logic, coordinates UI rendering, and handles VSN1 hardware communication (with batched LED commands)
- **`UIManager`**: Manages local TouchDesigner UI elements with bank-aware button states
- **`SlotManager`**: Handles parameter/ParGroup slot assignment, activation, clearing, bank switching, and parameter invalidation/recovery
- **`UndoManager`**: Manages undo/redo history for parameter changes, resets, slot operations, and batch updates
- **`RepoManager`**: Handles persistent storage of slot assignments and bank states
- **`ParameterValidator`**: Validates parameter compatibility, supports ParGroups with mixed valid/invalid parameters
- **`LabelFormatter`**: Smart label compression with ParGroup detection (`>` prefix) and priority formatting

**Key Features:**
- Mouse hover detection with automatic ParGroup vs single parameter detection
- **Full ParGroup support**: Control entire parameter groups (RGB, XYZ, etc.) simultaneously
- **Permissive slot assignment**: Allows saving parameters with expressions/exports (automatically skipped during manipulation)
- **Smart ParGroup handling**: 
  - Single-parameter groups treated as individual parameters
  - Invalid parameters within groups are skipped, not blocked
  - Type consistency validation (all parameters in group must be same type)
- Robust MIDI input processing with error handling
- Centralized parameter value calculations with type-specific handling
- Smart learning system implementation
- Multiple banks with independent slot management and memory
- Bank-aware UI updates with comprehensive state management
- Optimized VSN1 communication with batched LED updates
- Priority-based label formatting (ParGroup names with `>` prefix, preserves sequence block prefixes)
- Unified display architecture with thin renderer pattern
- Safe handling of empty/invalid MIDI configurations


## Contributing

When contributing to this project:
1. Test thoroughly with multiple MIDI controllers
2. Maintain compatibility with existing configurations
3. Document any new features or changes

---

*For technical support or feature requests, please refer to the project documentation or contact @function.str on Discord, or write an Issue ticket here on GitHub*
