---
layout: default
title: Home
---

# TouchDesigner Par Hover Control for Intech VSN1

<p style="color: #8fa3ff; font-size: 16px; margin-top: -10px; margin-bottom: 30px;">
  by <strong><a href="https://github.com/function-store" style="color: #8fa3ff; text-decoration: none;">Function Store</a></strong>
</p>

A [TouchDesigner](https://derivative.ca) component designed for the **[Intech Studio VSN1](https://intech.studio/se/shop/vsn1?sku=grid3-vsn1-r)** that provides intuitive parameter control using **endless relative MIDI encoders** and mouse hover interactions.

<div style="text-align: center; margin: 40px 0;">
  <img src="images/hoveredvsn1.jpg" alt="VSN1 Hardware" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);">
</div>

<div style="text-align: center; margin: 50px 0;">
  <a href="https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest/download/ParHoverMIDI_VSN1.tox" 
     style="display: inline-block; padding: 20px 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; text-decoration: none; border-radius: 10px; font-size: 22px; font-weight: bold; 
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); transition: all 0.3s ease;">
    ⬇️ Download ParHoverMIDI_VSN1.tox
  </a>
  <p style="margin-top: 20px; color: #bbb; font-size: 16px;">
    <a href="https://github.com/function-store/TD_ParHoverMIDI_VSN1/releases/latest" style="color: #8fa3ff; text-decoration: none;">Latest Release</a> • Includes Auto-Updater
  </p>
</div>

---

## ✨ Key Features

- **Hover-based Control** - Adjust any parameter by simply hovering your mouse over it
- **VSN1 Integration** - Full screen and LED feedback on VSN1 hardware
- **Parameter Slots** - Save parameters to buttons for instant recall across multiple banks
- **ParGroup Support** - Control entire parameter groups (RGB, XYZ) simultaneously
- **Smart Recovery** - Automatic detection and fixing of invalid parameters when operators move
- **Auto-Updates** - Built-in updater with one-click updates from GitHub
- **Flexible Precision** - Multiple step sizes with Fixed or Adaptive modes
- **Parameter Shortcuts** - Quick button combos for reset, set default, clamp, and more

---

## 📖 Documentation

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 30px; margin: 40px 0;">
  <div style="border: 2px solid #667eea; border-radius: 10px; padding: 25px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%); backdrop-filter: blur(10px);">
    <h3 style="margin-top: 0; color: #8fa3ff;">🚀 Getting Started</h3>
    <p style="color: #ddd;">Installation, MIDI setup, and first steps to get up and running quickly.</p>
    <a href="getting-started.html" style="color: #8fa3ff; font-weight: bold; text-decoration: none;">Read Guide →</a>
  </div>
  
  <div style="border: 2px solid #667eea; border-radius: 10px; padding: 25px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%); backdrop-filter: blur(10px);">
    <h3 style="margin-top: 0; color: #8fa3ff;">📚 User Guide</h3>
    <p style="color: #ddd;">Complete guide to all features: slots, banks, shortcuts, undo/redo, and customization.</p>
    <a href="user-guide.html" style="color: #8fa3ff; font-weight: bold; text-decoration: none;">Read Guide →</a>
  </div>
  
  <div style="border: 2px solid #667eea; border-radius: 10px; padding: 25px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%); backdrop-filter: blur(10px);">
    <h3 style="margin-top: 0; color: #8fa3ff;">🔍 Quick Reference</h3>
    <p style="color: #ddd;">Fast lookup tables for controls, shortcuts, parameters, and MIDI mappings.</p>
    <a href="reference.html" style="color: #8fa3ff; font-weight: bold; text-decoration: none;">View Reference →</a>
  </div>
  
  <div style="border: 2px solid #667eea; border-radius: 10px; padding: 25px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%); backdrop-filter: blur(10px);">
    <h3 style="margin-top: 0; color: #8fa3ff;">⚙️ Advanced Guide</h3>
    <p style="color: #ddd;">Recovery system, production setup, MIDI mapping details, and troubleshooting.</p>
    <a href="advanced.html" style="color: #8fa3ff; font-weight: bold; text-decoration: none;">Read Guide →</a>
  </div>
</div>

---

## 🎛️ Hardware Compatibility

**Primary Target:**
- **Intech Studio VSN1** - Full support with screen updates and LED feedback

**Requirements:**
- TouchDesigner 2023.12120+
- USB connection to MIDI controller
- For VSN1: Grid Editor open with exclusive access to port `9642`

<details markdown="1">
<summary><strong>Alternative Hardware (Other MIDI Controllers)</strong></summary>

- Generic MIDI controllers with endless encoders in relative mode
- Turn off `VSN1 Support` parameter for non-VSN1 controllers
- See [Getting Started - Setup for Other MIDI Controllers](getting-started.html#setup-for-other-midi-controllers) for details

</details>

---

## 🚀 Quick Start (VSN1)

1. **Install Grid Package**: Install `TouchDesigner Par Hover Control` from Grid Editor Package Manager. From the Cloud import `TouchDesigner Par Hover Control` profile to your VSN1!
   - *Not available in your Package Manager?* See [Getting Started - Grid Editor Setup](getting-started.html#grid-editor-setup-vsn1-users-only) for manual installation
2. **Download**: Get the latest `.tox` file using the button above
3. **Setup**: Set up your MIDI device, Drag into TouchDesigner at root `/`, set Device ID
4. **Use**: Hover over any parameter and twist your encoder!
5. **Explore**: There's much more this component can do, so keep on reading!

**👉 [Full installation guide](getting-started.html)**

---

## 🤝 Contributing

Contributions are welcome! Visit the [GitHub repository](https://github.com/function-store/TD_ParHoverMIDI_VSN1) to:
- Report issues
- Submit pull requests
- View source code
- Star the project ⭐

### Patreon

You can also support my work on [Patreon](patreon.com/function_store) where I have a lot of free and exclusive stuff!

---

## 🙏 Contributors & Acknowledgments

<div style="border: 2px solid #667eea; border-radius: 10px; padding: 25px; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); margin: 30px 0;">

**Main Developer:**
- **[Function Store](https://www.functionstore.xyz/link-in-bio)** - Project creator and lead developer

**Special Thanks:**
- **[Greg Orca](https://www.instagram.com/greg_orca/)** - Valuable feedback and ongoing support
- **[Dániel Pásztor](https://github.com/danim1130)** - Queued screen updates and GitHub Actions implementation
- **[Intech Studio](https://intech.studio/)** - General support and hardware collaboration
- **[TheTouchLab](https://www.instagram.com/thetouchlab/)** - Network Editor mouse position tracking

</div>

---

## 📝 License

See [LICENSE](https://github.com/function-store/TD_ParHoverMIDI_VSN1/blob/main/LICENSE) file for details.

---

<div style="text-align: center; margin-top: 60px; padding-top: 30px; border-top: 2px solid #444;">
  <p style="color: #bbb;">
    <strong>Support:</strong> Contact @function.str on Discord or <a href="https://github.com/function-store/TD_ParHoverMIDI_VSN1/issues" style="color: #8fa3ff;">open an issue</a>
  </p>
  <p style="color: #888; font-size: 14px; margin-top: 10px;">
    Made with ❤️ for the TouchDesigner community
  </p>
</div>

