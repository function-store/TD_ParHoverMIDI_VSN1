# HoveredMidiRelative

A TouchDesigner component for intuitive parameter control using **endless relative MIDI encoders** and mouse hover interactions. **This component only works with endless relative MIDI knobs (such as the [Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r), but should work with others) - standard potentiometers will not function.**

## Overview

HoveredMidiRelative enables seamless parameter adjustment in TouchDesigner by combining mouse hover detection with MIDI controller input. Simply hover your mouse over any parameter and use your MIDI controller to make precise adjustments without clicking or dragging. The system controls one parameter at a time based on your mouse hover position.

> Relative MIDI means the device sends a value less or greater than 64 to indicate movement in either direction. The greater the difference, the bigger the movement. The sensitivity is configurable for VSN1 for example.

## Features

- **Hover-based Parameter Control**: Adjust any parameter by hovering your mouse over it
- **Parameter Persistence Mode**: Lock parameters for continuous adjustment without hovering
- **MIDI Integration**: Works with endless MIDI encoders in relative mode
- **Smart Learning System**: Automatically assign MIDI button mappings for step adjustment and main knob MIDI index
- **Adjustable Precision**: Change adjustment step sizes using MIDI buttons
- **Parameter Reset**: Hold button to reset parameters to default values
- **Hardware Support**: Should work with any endless/relative encoder, optimized for [Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r) with specialized support
- **Real-time Feedback**: Visual feedback on VSN1's built-in screen during parameter adjustments
  
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
  - Import `TouchDesigner Hover Param Adjustment` from Intech Cloud for VSN1R/L

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

## Special MIDI Functions

Beyond step size adjustment, there are two special MIDI button functions:

### Parameter Persistence (`Par Persist Index`)
- **While hovering over a parameter**: Press this MIDI button to "lock" the parameter for continuous adjustment
- **Locked mode**: The parameter remains selected even when moving your mouse away - you can adjust it without hovering
- **Exit locked mode**: Press the button again while NOT hovering over any parameter to return to normal hover mode
- **Override locked parameter**: Press the button while hovering over a different parameter to lock that one instead

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
- **`VSN1 Screen Update`**: Enables updating VSN1 screen displaying adjusted parameter and value (circle size between param normMin/Max values), using websocket communication --- requires Grid Editor to be open!
- **`Reset Comm`**: In case GRID Editor reports websocket connection is not active try pulsing this.

## Known Issues
- VSN1 screen not updating consistently due to reaching character limit (too long param name, or value)
- VSN1 screen glitching out (too quick updates? firmware issue?)

## Future Plans / Roadmap

### Multiple Parameter Slots
- **Different locked slots on buttons**: Assign multiple MIDI buttons as parameter slot holders
- **Hot-swappable assignments**: Hover over a parameter and press a slot button to assign it to that slot
- **Quick parameter switching**: Switch between multiple locked parameters without re-hovering
- **Workflow enhancement**: Enable complex multi-parameter workflows with instant parameter access

This feature will allow users to have several parameters "ready" on different buttons, making it possible to quickly jump between frequently adjusted parameters in complex TouchDesigner projects.

## Development

### Extension Scripts
The `HoveredMidiRelativeExt.py` file contains the core logic for:
- Mouse hover detection
- MIDI input processing
- Parameter value calculations
- Learning system implementation
- VSN1 screen update support



## Contributing

When contributing to this project:
1. Test thoroughly with multiple MIDI controllers
2. Maintain compatibility with existing configurations
3. Document any new features or changes

---

*For technical support or feature requests, please refer to the project documentation or contact @function.str on Discord, or write an Issue ticket here on GitHub*
