# TouchDesigner Par Hover Control for VSN1

A [TouchDesigner](https://derivative.ca) component designed for the **[Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r)** that provides intuitive parameter control using **endless relative MIDI encoders** and mouse hover interactions. While optimized for VSN1, it can be made compatible with other endless relative MIDI controllers.

![VSN1 Hardware](https://github.com/function-store/TD_ParHoverMIDI_VSN1/blob/main/docs/images/hoveredvsn1.jpg)

## ✨ Key Features

- **Hover-based Control** - Adjust any parameter by simply hovering your mouse over it
- **VSN1 Integration** - Full screen and LED feedback on VSN1 hardware
- **Parameter Slots** - Save parameters to buttons for instant recall across multiple banks
- **ParGroup Support** - Control entire parameter groups (RGB, XYZ) simultaneously
- **Parameter Shortcuts** - Quick button combos for reset, set default, clamp, and more
- **Flexible Precision** - Multiple step sizes with Fixed or Adaptive modes
- **Network Zoom Navigation** - Smooth zoom and pan in network editor when no parameter is active
- **Smart Recovery** - Automatic detection and fixing of invalid parameters when operators move
- **Auto-Updates** - Built-in updater with one-click updates from GitHub releases

## 🚀 Quick Start

### For VSN1 Users

1. **Install Grid Package** (one-time setup):
   - Newer Grid Editor versions: Install `TouchDesigner Par Hover Control` directly from Package Manager
   - Older versions: Clone repo, build, and add manually (see [Getting Started](docs/getting-started.md))
   - Search for, and import the `TouchDesigner Par Hover Control` configuration from Grid Editor to your VSN1 device

2. **Download** [`ParHoverMIDI_VSN1.tox`](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest/download/ParHoverMIDI_VSN1.tox) from the [latest release](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest)

3. **Setup in TouchDesigner**:
   - Drag the `.tox` into your project at **root `/`** (recommended location)
   - **⚠️ Important**: Only one component instance per project, and only one project open at a time (communication/architecture limitation)
   - **Keep Grid Editor open** (component auto-launches it, needs exclusive access to port `9642`)
   - Open TD's [MIDI Device Mapper](https://docs.derivative.ca/MIDI_Mapper_Dialog), set the VSN1 (*Intech Grid MIDI Device*) as Input and Output device, and note your Grid device's **Device ID**
   - Set this `Device ID` in component's **VSN1/UI** parameter page

4. **Start Using**:
   - Hover over any parameter and twist your encoder to adjust it!
   - Change step size with buttons under the LCD screen
   - Save parameters to slots with long-press of primary buttons
   - Switch between banks by long-pressing the step buttons
   - And much more! See [User Guide](docs/user-guide.md) for all features

> **Using other MIDI controllers?** This component works with any endless/relative MIDI encoder. See [Getting Started - Other Controllers](docs/getting-started.md#setup-for-other-midi-controllers) for setup instructions.

## 📖 Documentation

**[📚 View Full Documentation Site](https://function-store.github.io/TD_ParHoverMIDI_VSN1/)** *(recommended)*

Or browse the docs directly:
- **[Getting Started](docs/getting-started.md)** - Installation, MIDI setup, and first steps
- **[User Guide](docs/user-guide.md)** - Features, slots/banks, shortcuts, customization
- **[Advanced](docs/advanced.md)** - Recovery system, production setup, MIDI mapping, troubleshooting

## 🎛️ Hardware Compatibility

**Primary Target:**
- **Intech Studio VSN1** - Full support with screen updates and LED feedback

**Alternative Hardware:**
- Generic MIDI controllers with endless encoders in relative mode (no visual feedback)
- Turn off `VSN1 Support` parameter for non-VSN1 controllers

**Requirements:**
- TouchDesigner 2023.12120+
- USB connection to MIDI controller
- For VSN1: Grid Editor open with exclusive access to port `9642`

## 🔄 Updates

The component includes a built-in updater accessible from the **About** page:

1. Open the component's **About** parameter page
2. Check for and install new versions with one click
3. View changelog before updating

**Best Practice:** Use the **`Externalize Component`** button in the About page before updating. This one-click setup preserves your slot data across all future updates. See [Best Practices for Update Compatibility](docs/getting-started.md#best-practices-for-update-compatibility) for details.

## 🤝 Contributing

Contributions are welcome! Please:
1. Test thoroughly with multiple MIDI controllers
2. Maintain compatibility with existing configurations
3. Document any new features or changes

See [Development](docs/advanced.md#development) for project structure details.

## 📝 License

See [LICENSE](LICENSE) file for details.

---

**Support**: Contact @function.str on Discord or [open an issue](https://github.com/function-store/TD_ParHoverMIDI_VSN1/issues)
