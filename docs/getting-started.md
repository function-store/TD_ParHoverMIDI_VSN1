# Getting Started

Complete installation and setup guide for TouchDesigner Par Hover Control for VSN1.

## Installation

### Grid Editor Setup (VSN1 Users Only)

**1. Install the Grid Package:**

**Option A - From Package Manager (Recommended for newer Grid Editor versions):**

1. Open Grid Editor
2. Go to the Package Manager panel
3. Look for `TouchDesigner Par Hover Control` in the available packages
4. Click Install

> **Note**: If the package is not available in your Grid Editor version, use Option B below.

**Option B - Manual Installation (for older Grid Editor versions or development):**

```bash
# Clone the repository
git clone https://github.com/function-store/TD_ParHoverMIDI_VSN1.git

# Navigate to the root folder
cd TD_ParHoverMIDI_VSN1

# Install dependencies
npm i

# Build the package
npm run build
```

Then in Grid Editor:
1. Go to the Package Manager panel
2. Click `+ Add external package` and add the **root** path (e.g., `C:\Users\...\TD_ParHoverMIDI_VSN1`)
3. Approve the package when it appears

**2. Import VSN1 Configuration:**

1. On your VSN1 device in Grid Editor, import `TouchDesigner Par Hover Control` configuration
2. Keep Grid Editor open at all times when using VSN1 (requires exclusive access to port `9642`)

> The TouchDesigner component automatically attempts to open Grid Editor on startup

### TouchDesigner Setup

**1. Download Component:**

Download `ParHoverMIDI_VSN1.tox` from the [latest release](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest)

**2. Add to Project:**

1. Connect your MIDI controller to your system
2. Drag `ParHoverMIDI_VSN1.tox` into your TouchDesigner project at **root `/`** (recommended location)

> **⚠️ Important Limitation**: Only one component instance is allowed per project file, and only one TouchDesigner project with this component should be open at a time. This is due to communication and architecture limitations. Always place the component at the project root `/` for best compatibility.

**3. Configure MIDI:**

1. **Set up MIDI Device in TouchDesigner:**
   - Open TouchDesigner's MIDI Device Mapper (Dialogs → MIDI Mapper)
   - Ensure your Grid/VSN1 MIDI device is visible and active and set as both Input and Output
   - Note the **Device ID** (this is critical for the next step)

2. **Configure Component:**
   - Open the component's **VSN1/UI** parameter page
   - **⚠️ CRITICAL**: Set the `Device ID` parameter to match the device ID from MIDI Mapper
   - This links the component to your physical MIDI controller

<details>
<summary><h3 style="display: inline;">Setup for Other MIDI Controllers</h3></summary>

If you're using a different endless/relative MIDI encoder (not VSN1):

1. **Download** `ParHoverMIDI_VSN1.tox` from the [latest release](https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest)
2. **Drag** the `.tox` into your TouchDesigner project (suggested at root `/`)
3. **Disable VSN1 features**:
   - Turn off `VSN1 Support` parameter in **VSN1/UI** page to disable screen/LED features
   - No Grid Editor required
4. **Set Device ID**:
   - Note your device's ID from TD's MIDI Device Mapper
   - Set the same ID in component's **VSN1/UI** parameter page
5. **Configure mappings**:
   - Use Learn Mode: Hover over mapping fields and move your MIDI controls
   - Or set MIDI indices manually in the **Mapping** tab
   - Configure step sizes (default: 0.001, 0.01, 0.1, 1)
   - See [Advanced Guide - MIDI Mapping](advanced.md#midi-mapping-configuration) for details
6. **Start using**: Hover over any parameter and twist your encoder!

> **Note**: Endless/relative encoders are required. Standard potentiometers will not work as intended.

</details>

## Verify It's Working

Let's test that everything is set up correctly:

1. **Hover your mouse** over any numeric parameter in TouchDesigner (e.g., a `tx` translate parameter on any operator)
2. **Twist your MIDI encoder/knob** - the parameter value should change in real-time!
3. **Success!** Your setup is complete and working

**Troubleshooting:**
- Parameter not changing? Check Device ID matches in MIDI Mapper and component's **VSN1/UI** page
- Verify your controller sends endless/relative MIDI (not standard potentiometer values)
- For VSN1: Ensure Grid Editor is open and the package is loaded on your device

## What's Next? Discover All the Features!

You've got the basics working - but there's so much more! This component has powerful features for streamlined parameter control:

### 🎯 Core Features You'll Use Daily

- **[Parameter Slots](user-guide.md#parameter-slots-system)** - Save parameters to buttons for instant recall without hovering
- **[Multiple Banks](user-guide.md#multiple-banks)** - Organize slots into banks (e.g., Bank 0 = lighting, Bank 1 = audio)
- **[Parameter Shortcuts](user-guide.md#parameter-shortcuts)** - Quick button combos: reset, set default, clamp, and more
- **[Step Sizes & Modes](user-guide.md#step-modes)** - Adjust precision with Fixed or Adaptive step modes
- **[Undo/Redo](user-guide.md#undoredo-operations)** - Undo any parameter change with `Ctrl+Z` / `Cmd+Z`

### 🚀 Advanced Capabilities

- **[ParGroup Control](user-guide.md#parameter-slots-system)** - Control entire parameter groups (RGB, XYZ) simultaneously
- **[Parameter Recovery](advanced.md#parameter-recovery-system)** - Automatic recovery when operators are moved/renamed
- **[UI Highlighting](user-guide.md#ui-parameter-highlighting)** - Visual feedback in TouchDesigner interface
- **[Full Customization](user-guide.md#customization-parameters)** - Extensive options to tailor behavior to your workflow

**👉 Continue to the [User Guide](user-guide.md) to learn how to use all these features!**

---

## Best Practices for Update Compatibility

To ensure your slot data and configurations are preserved when updating the component:

### Automatic Setup with "Externalize Component" Button (Recommended)

The easiest way to set up for seamless updates:

1. Open the component's **About** parameter page
2. Pulse the **`Externalize Component`** button
3. This automatically:
   - Saves the component as an external `.tox` file to your Palette folder
   - Converts the component to an external reference in your project
   - Creates and links an external Slots Repo table in your project
   - Ensures all future updates preserve your slot assignments and configurations

**Benefits:**
- One-click setup for update compatibility
- Persistent slot data across all updates
- Works across multiple projects using the same external `.tox`
- Component updates apply everywhere automatically

### Manual Setup (Advanced Users)

If you prefer manual control:

**External Repo:**
1. Use the `Create` custom parameter to create an external Repo table (e.g., `/repo_storage`)
2. The `Slots Repo` parameter will automatically point to this external table
3. Component updates won't affect your saved slots

**External .tox:**
1. Save component as external `.tox` to `Palette/FNStools_ext/ParHoverMIDI_VSN1.tox`
2. In each project, drag this `.tox` as an **external component** (shows reference icon)
3. Enable the `External .tox` parameter in the component

> The built-in updater (About page) also uses the Palette folder structure for easy external setup

## Next Steps

- **[User Guide](user-guide.md)** - Learn all features, shortcuts, and customization options
- **[Advanced](advanced.md)** - Parameter recovery, MIDI mapping details, troubleshooting

## Troubleshooting

**MIDI not responding:**
- Check Device ID is set correctly in Mapping tab
- Verify MIDI device is active in TD's MIDI Device Mapper
- Ensure you're using endless/relative MIDI encoders (not standard pots)

**VSN1 screen not updating:**
- Ensure Grid Editor is open
- Check Grid Editor has exclusive access to port `9642`
- Try pulsing `Reset Comm` parameter

**Grid Editor won't open automatically:**
- Check installation path matches common locations
- Open Grid Editor manually

---

[← Back to README](../README.md) | [User Guide →](user-guide.md)

