# HoveredMidiRelative

A TouchDesigner component for intuitive parameter control using **endless relative MIDI encoders** and mouse hover interactions. **This component only works with endless relative MIDI knobs (such as the [Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r), but should work with others) - standard potentiometers will not function.**

## Overview

HoveredMidiRelative enables seamless parameter adjustment in TouchDesigner by combining mouse hover detection with MIDI controller input. Simply hover your mouse over any parameter and use your MIDI controller to make precise adjustments without clicking or dragging. The system controls one parameter at a time based on your mouse hover position.

> Relative MIDI means the device sends a value less or greater than 64 to indicate movement in either direction. The greater the difference, the bigger the movement. The sensitivity is configurable for VSN1 for example.

## Features

- **Hover-based Parameter Control**: Adjust any parameter by hovering your mouse over it
- **Multiple Parameter Slots**: Assign parameters to MIDI buttons for instant access and switching
- **MIDI Integration**: Works with endless MIDI encoders in relative mode
- **Smart Learning System**: Automatically assign MIDI button mappings for step adjustment and main knob MIDI index
- **Enhanced Parameter Support**: Full support for Numeric, Menu, Toggle, and Pulse parameters
- **Adjustable Precision**: Change adjustment step sizes using MIDI buttons
- **Parameter Reset**: Hold button to reset parameters to default values
- **Robust Error Handling**: Graceful handling of empty/invalid MIDI configurations
- **Hardware Support**: Should work with any endless/relative encoder, optimized for [Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r) with specialized support
- **Real-time Feedback**: Visual feedback on VSN1's built-in screen during parameter adjustments
- **LED Feedback**: Visual feedback on VSN1 LEDs showing active parameter slots

## Hardware Compatibility

### Supported Controllers
- **Generic MIDI Controllers**: Compatible with endless encoders in relative mode
- **MIDI Button Controllers**: For step size adjustment functionality (optional enhancement)
- **intech.studio VSN1**: Full native support with optimized mappings (endless encoders) and screen update

### Requirements
- TouchDesigner (2023.11880+)
- **MIDI controller with endless relative encoders** (absolute controls will not work)
- USB or MIDI interface connection
- **For VSN1 display updates**: 
  - Install and activate the [websocket package](https://github.com/intechstudio/package-websocket?tab=readme-ov-file#installation)
  - Grid Editor must be open with exclusive access to port 9834 (no other communication on this port)
  - Import `TouchDesigner Hover Param Adjustment` from the Grid Editor Link [link](grid-editor://?config-link=xRPvAgRRc1AobWO2HtY) or look for it in the Cloud

## Installation

0. Connect your MIDI controller to your system
1. Configure MIDI settings in TouchDesigner (Dialogs -> MIDI Mapper)
2. Download the latest release from the `modules/release/` directory
3. Drag `HoveredMidiRelative.tox` into your TouchDesigner project

## Quick Start

1. **Setup**: Place the HoveredMidiRelative component in your network
2. **MIDI Configuration**: Ensure your MIDI controller is recognized by TouchDesigner
3. **MIDI Setup**: On the component, set your `Device ID` and MIDI `Channel`
4. **MIDI Mapping**: Map MIDI indices to functions using the custom parameters. Use the Sequence parameter +/- buttons to change the number of mapped steps.
   - **Manual**: Type the MIDI note/control indices to the custom parameters
   - **Learning Mode**: Activate the hover-learning function to map controls by turning on `Learn`, hover over an empty mapping and move your MIDI knobs/buttons.
   - **Preset mapping for VSN1**: Pulse the parameter `Use Defaults for VSN1`
5. **Modify Step Size**: When using `Learning Mode` the step sizes will be automatically set to 1, 0.1, ...
6. **Adjust Step Size**: Use assigned MIDI buttons to cycle through different step sizes for fine/coarse control 
7. **Usage**: Hover over any parameter and twist your MIDI controller to adjust that specific parameter's value
8. Check [Parameter Slots System](#parameter-slots-system) to save and recall parameters to control!

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

### Parameter Reset (`Reset Par Index`)
- **Hold this MIDI button**: While hovering over any parameter for the specified time duration
- **Result**: The parameter will reset to its default value
- **Duration**: Configurable via the `Reset Hold Length` parameter

## Customization Parameters

The following parameters are available to further customize the functionality of the component:
- **`Step Size`**: Adjustable in each `Step` block.
- **`Persist Step` toggle**: When this is off, the step will be set to default when not holding any step button. When on, it will save the last used step.
- **`Default Step Size`**: Step size when Persist Step is off and not holding any step button. Set this to zero to avoid accidental parameter adjustments when not holding any button.
- **`Reset Hold Length`**: Holding the assigned reset button for this specified time will reset hovered parameter to its default value.
- **`VSN1 Support`**: Enables VSN1 screen updates and LED feedback, displaying adjusted parameter and value (circle size between param normMin/Max values), using websocket communication --- requires Grid Editor to be open!
- **`Reset Comm`**: In case GRID Editor reports websocket connection is not active try pulsing this.

## Known Issues
- Screen updates can be laggy (probable cause: Grid MIDI RX callbacks that are used for LED updates)

## Future Plans / Roadmap

### Enhanced Slot Management
- ✅ **LED feedback for active slots**: Implemented - LEDs show which slot is currently active
- **Enhanced visual indicators**: Color-coded LEDs or screen indicators for different slot states
- **Slot persistence improvements**: Better handling of slot assignments across sessions

## Development

### Extension Scripts
The `HoveredMidiRelativeExt.py` file has been refactored into a modular architecture:

**Core Classes:**
- **`HoveredMidiRelativeExt`**: Main extension class with TouchDesigner integration
- **`MidiMessageHandler`**: Processes MIDI input and manages LED feedback
- **`ScreenManager`**: Handles VSN1 screen updates and display formatting
- **`ParameterValidator`**: Validates parameter compatibility and learning eligibility

**Key Features:**
- Mouse hover detection and parameter tracking
- Robust MIDI input processing with error handling
- Centralized parameter value calculations
- Smart learning system implementation
- VSN1 screen updates and LED feedback
- Safe handling of empty/invalid MIDI configurations


## Contributing

When contributing to this project:
1. Test thoroughly with multiple MIDI controllers
2. Maintain compatibility with existing configurations
3. Document any new features or changes

---

*For technical support or feature requests, please refer to the project documentation or contact @function.str on Discord, or write an Issue ticket here on GitHub*
