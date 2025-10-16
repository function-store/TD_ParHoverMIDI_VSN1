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
- **Multiple Parameter Slots**: Assign parameters to VSN1 buttons for instant access and switching
- **Multiple Banks**: Organize slots into separate banks using VSN1 buttons for expanded parameter control
- **Smart Learning System**: Automatically assign VSN1 button mappings for step adjustment and main knob control
- **Enhanced Parameter Support**: Full support for Numeric, Menu, Toggle, and Pulse parameters
- **Adjustable Precision**: Change adjustment step sizes using VSN1 step buttons
- **Parameter Reset**: Hold VSN1 button to reset parameters to default values
- **Real-time VSN1 Feedback**: Full integration with VSN1's built-in screen and LED system
  - **LED Feedback**: Color-coded LEDs showing slot states (dark/dim/bright)
  - **Screen Display**: Parameter names, values, and bank indicators on VSN1 screen
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

**Import the VSN1 Configuration:**
1. In the Grid Editor cloud search for `TouchDesigner Par Hover Control` and import it on your **VSN1** device.
2. Keep Grid Editor open at all times when using VSN1 (exclusive access to port `9642` required)

### TouchDesigner

1. Connect your MIDI controller to your system
2. Configure MIDI settings in TouchDesigner (Dialogs -> MIDI Mapper)
3. Download `ParHoverMIDI_VSN1.tox` from the [latest release](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest)
4. Drag `ParHoverMIDI_VSN1.tox` into your TouchDesigner project (suggested `/` root)
5. Have Grid Editor open at all times when using Intech hardware (see next section)

## Quick Start
0. Download `ParHoverMIDI_VSN1.tox` from the [latest release](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest)
1. **Setup**: Place the `ParHoverMIDI_VSN1.tox` component in your network (suggested at root `/`)
2. **MIDI Configuration**: Ensure your MIDI device is recognized in TouchDesigner's Device Manager
3. **MIDI Setup**: Set your `Device ID` and MIDI `Channel` in the component parameters
1. **VSN1 Settings**: On the component, pulse `Use Defaults for VSN1` to automatically configure all mappings
2. **Alternative Manual Setup** (for non-VSN1 users):
   - Map MIDI indices manually using the custom parameters
   - Use `Learn` mode to map controls by hovering over empty mappings and moving your MIDI knobs/buttons
3. **Modify Step Size**: When using `Learning Mode` the step sizes will be automatically set to 0.001, 0.01, 0.1, 1
4. **Adjust Step Size**: Use assigned MIDI buttons to cycle through different step sizes for fine/coarse control 
5. **Usage**: Hover over any parameter and twist your MIDI controller to adjust that specific parameter's value
6. Check [Parameter Slots System](#parameter-slots-system) to save and recall parameters to control!
7.  **Multiple Banks**: Use [Multiple Banks](#multiple-banks) to organize slots into separate banks for expanded control

## Special MIDI Functions

Beyond step size adjustment, there are two special MIDI button functions:

### Parameter Slots System
The component supports multiple parameter slots that can be assigned to different MIDI buttons for quick access:

**Slot Assignment**:
- **Hover over a parameter** you want to assign to a slot
- **Long-press a slot button** (configured in the Slots sequence) to assign the hovered parameter to that slot
- **The parameter is now "stored"** in that slot for quick access
- **Clear a slot**: Long-press any slot button while not hovering over any parameter to free up that slot (and return it to **normal hover mode**)

**Slot Activation**:
- **Press any assigned slot button** to activate that parameter slot
- **The stored parameter becomes active** for adjustment without needing to hover
- **VSN1 screen updates** to show the active slot parameter
- **VSN1 LED feedback**: The active slot button lights up, previous slot LED turns off automatically

**Return to Hover Mode**:
- **Press an empty slot button** (one without an assigned parameter) to return to normal hover mode
- **All VSN1 slot LEDs turn off** when returning to hover mode

> Parameter slots are saved with the project file / component.

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

### Parameter Reset (`Reset Par Index`)
- **Hold this MIDI button**: While hovering over any parameter for the specified time duration
- **Result**: The parameter will reset to its default value
- **Duration**: Configurable via the `Reset Hold Length` parameter

### Parameter Pulse (`Pulse Index`)
- **Press this MIDI button**: While hovering over a parameter
- **For Pulse parameters**: Triggers the pulse action
- **For Toggle parameters**: Toggles the parameter on/off
- **Other parameter types**: No action (returns false)

## Customization Parameters

The following parameters are available to further customize the functionality of the component:
- **`Step Size`**: Adjustable in each `Step` block.
- **`Persist Step` toggle**: When this is off, the step will be set to default when not holding any step button. When on, it will save the last used step.
- **`Default Step Size`**: Step size when Persist Step is off and not holding any step button. Set this to zero to avoid accidental parameter adjustments when not holding any button.
- **`Reset Hold Length`**: Holding the assigned reset button for this specified time will reset hovered parameter to its default value.
- **`VSN1 Support`**: Enables VSN1 screen updates and LED feedback, displaying adjusted parameter and value (circle size between param normMin/Max values), using websocket communication --- requires Grid Editor to be open!
- **`Label Display Mode`**: Choose between "Compressed" (removes vowels/spaces) or "Truncated" (simple cut-off) for parameter label formatting on limited displays
- **`Reset Comm`**: In case GRID Editor reports websocket connection is not active try pulsing this.
- **`Knob LED Update`**: Choose between "Off", "Value" and "Step" to determine what is indicated on the knob LEDs of VSN1. **NOTE**: Currently when set to "Value", laggy updates can be observed on the hardware unit.

## VSN1 Visual Feedback

The VSN1 provides comprehensive visual feedback through LEDs and screen elements:

### **Button LED States**:
- **Dark**: Slot is free and available for assignment (hover mode)
- **Dim**: Slot has a parameter assigned but is not currently active
- **Bright**: Slot is currently active and controlling this parameter

### **Screen Outline Colors**:
- **Color outline**: Currently in hover mode - move mouse to select parameters
- **White outline**: Currently in slot mode - a parameter slot is active

### **Bank Indicators**:
- **Screen display**: Shows current bank number (e.g., "Bank 0", "Bank 1")
- **Button updates**: Slot button labels and LEDs update when switching banks
- **UI indicator**: TouchDesigner UI shows current bank number

### **Step Size Indicators**:
- **Screen display**: Shows current step value when step size changes

### **Knob LEDs**: 
- **Knob ring LEDs** show visual feedback of value-based gradual fill or step-based indicators, depending on setting.

This visual system makes it immediately clear whether you're in hover mode or slot mode, which bank you're currently using, which slots are available, occupied, or active, and what precision level you're currently using for parameter adjustments.

## Known Issues
- Screen updates can be laggy (it is trying its best though)

## Future Plans / Roadmap

### Enhanced Slot Management
- ✅ **LED feedback for active slots**: Implemented - LEDs show which slot is currently active
- ✅ **Multiple banks**: Implemented - organize slots into separate banks for expanded control
- ✅ **Bank memory**: Implemented - each bank remembers its last active slot and assignments
- ✅ **Visual bank indicators**: Implemented - screen and UI show current bank number
- **Enhanced visual indicators**: Additional color-coded LEDs or screen indicators for different slot states
- **Slot persistence improvements**: Better handling of slot assignments across sessions


## Known Issues
- When **`Knob LED Update`** is set to "Value", laggy updates can be observed on the hardware unit, but it does not affect actual value updates.

## Development

### Project Structure
The codebase has been refactored into a modular architecture for better maintainability:

```
scripts/HoveredMidiRelative/
├── constants.py              # All constants and enums
├── validators.py             # Parameter validation logic
├── formatters.py             # Label and value formatting utilities
├── handlers.py               # MIDI message processing
├── managers/
│   ├── slot_manager.py       # Parameter slot operations
│   ├── display_manager.py    # Unified display logic coordinator
│   ├── vsn1_manager.py       # VSN1 hardware integration
│   └── ui_manager.py         # Local UI element management
└── HoveredMidiRelativeExt.py # Main extension class
```

> This repo also contains the Grid package code for a monolithic repo, and is based on the [example package](https://github.com/intechstudio/package-websocket).

**Core Components:**
- **`HoveredMidiRelativeExt`**: Main extension class with TouchDesigner integration
- **`MidiMessageHandler`**: Processes MIDI input (steps, knobs, pulses, slots, banks)
- **`DisplayManager`**: Centralizes all display logic and coordinates renderers
- **`VSN1Manager`**: Handles VSN1 screen updates and LED feedback (with batched LED commands)
- **`UIManager`**: Manages local TouchDesigner UI elements with bank-aware button states
- **`SlotManager`**: Handles parameter slot assignment, activation, clearing, and bank switching
- **`ParameterValidator`**: Validates parameter compatibility and learning eligibility
- **`LabelFormatter`**: Smart label compression with priority for parameter groups and sequence block indices

**Key Features:**
- Mouse hover detection and parameter tracking
- Robust MIDI input processing with error handling
- Centralized parameter value calculations with type-specific handling
- Smart learning system implementation
- Multiple banks with independent slot management and memory
- Bank-aware UI updates with comprehensive state management
- Optimized VSN1 communication with batched LED updates
- Priority-based label formatting (preserves parameter group suffixes and sequence block prefixes)
- Unified display architecture with thin renderer pattern
- Safe handling of empty/invalid MIDI configurations


## Contributing

When contributing to this project:
1. Test thoroughly with multiple MIDI controllers
2. Maintain compatibility with existing configurations
3. Document any new features or changes

---

*For technical support or feature requests, please refer to the project documentation or contact @function.str on Discord, or write an Issue ticket here on GitHub!*
