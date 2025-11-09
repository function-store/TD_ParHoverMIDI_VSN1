---
layout: default
title: Advanced Guide
nav_order: 3
---

# Advanced Guide

Advanced features, MIDI mapping, troubleshooting, and development information.

## Table of Contents

- [Parameter Recovery System](#parameter-recovery-system)
- [Update Compatibility & External Setup](#update-compatibility--external-setup)
- [MIDI Mapping Configuration](#midi-mapping-configuration)
- [Known Issues](#known-issues)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Parameter Recovery System

Automatic detection and recovery when operators are moved, renamed, or deleted.

### Automatic Detection

The system scans for invalid parameters:
- When activating a slot
- When switching banks
- When attempting parameter interaction
- After certain background operations

### Recovery Dialog

When invalid parameters are detected, a dialog appears with three options:

**Fix**
- Edit path to point to new location/name
- **Batch update**: Automatically updates all other slots with same operator path
- **Smart matching**: Handles exact matches and child operator paths
- Example: Update `/project1/geo1` to `/project1/effects/geo1` across all slots

**Clear**
- Remove invalid parameter from this specific slot only
- **Single operation**: Only affects current slot
- Use for cleaning up individual mistakes

**Clear All**
- Remove invalid parameter from all related slots
- **Batch clear**: Clears all slots with same operator path
- Use when operator is permanently deleted

### Sequential Processing

If multiple parameters are invalid, dialogs appear one at a time to prevent overwhelming you.

### Common Use Cases

| Scenario | Recommended Action |
|----------|-------------------|
| Operator moved | **Fix** - Updates all related slots |
| Operator renamed | **Fix** - Updates paths in bulk |
| Operator deleted | **Clear All** - Removes from all slots |
| Single slot mistake | **Clear** - Remove only that slot |
| Project reorganization | **Fix** - Update paths in bulk |

### Batch Operations

- **Fix**: Updates all slots pointing to same operator automatically
- **Clear**: Affects only the current slot
- **Clear All**: Clears all slots with parameters from that operator
- **Child paths**: Automatically updates child operators (e.g., `/project1/test1/circle1` updates when `/project1/test1` moves)

### Undo Support

All recovery operations are undoable:
- Undo Fix: `Ctrl+Z`/`Cmd+Z` reverts batch path updates
- Undo Clear: Restores single cleared slot
- Undo Clear All: Restores all cleared slots

### Visual Feedback

- **`_INVALID_` message**: Displays when accessing invalid parameters
- **Dialog prompts**: Clear interface for recovery actions
- **Seamless recovery**: After fixing, operation continues normally

### Manual Table Editing

Advanced users can directly edit slot storage tables:

**Table Location:**
- Internal: `SlotsRepo` inside component
- External: Referenced by `Slots Repo` parameter

**Table Structure:**
- Each bank has its own table
- Columns:
  - `path`: Operator path (e.g., `/project1/geo1`)
  - `name`: Parameter name (e.g., `tx`)
  - `type`: `Par` or `ParGroup`
  - `active`: Active slot indicator (`0` or `1`)

**Use Cases:**
- Bulk editing multiple slots
- Scripting configurations
- Transferring setups between projects
- Advanced parameter management

**Important:**
- Ensure proper formatting to maintain compatibility
- Backup tables before manual editing
- Invalid entries will trigger recovery dialogs

## Update Compatibility & External Setup

Comprehensive guide to external storage and seamless updates.

### Automatic Slot Data Protection

**Already Done For You:**

The component automatically protects your work on first launch:
- ✅ External Slots Repo is **automatically created** at `/project1/ParHoverMIDI_VSN1_SlotsRepo`
- ✅ Your slot assignments are stored outside the component
- ✅ Updates will never affect your saved slots
- 🔧 Can be disabled via the `Auto-Create Repo` parameter if you prefer manual control

**Customizing the Repo Location:**
1. Set `Auto-Create Repo` to off
2. Use the `Create` custom parameter to create an external Repo at your preferred location
3. Point the `Slots Repo` parameter to your custom table

### Full External Setup with "Externalize Component"

For **maximum update compatibility** and multi-project workflows:

**The One-Click Solution:**
1. Open the component's **About** parameter page
2. Pulse the **`Externalize Component`** button
3. Done! ✅

**What It Does:**
- Saves the component as an external `.tox` file to `Palette/FNStools_ext/`
- Converts the component to an external reference in your project
- Creates and links an external Slots Repo (if not already external)
- Ensures all future updates preserve your configurations

**Benefits:**
- 🚀 One-click setup for full external workflow
- 🔄 Use the same component across multiple projects
- ⚡ Update the component once, updates apply everywhere
- 💾 Complete persistence of all data and settings

### In-Component Updater

Built-in updater in the **About** parameter page:

**How to Update:**
1. The UI icon in TouchDesigner's top-right corner turns **yellow** when updates are available
2. Click the icon and navigate to **About** page
3. Review the changelog to see what's new
4. Click **Update** to install with one click
5. Component downloads to `Palette/FNStools_ext/`

**Update Safety:**
- Automatic backup of current version
- Preserves all slot data (thanks to external repo)
- Preserves all parameter settings
- Works seamlessly with external `.tox` setup

### Manual External Setup (Advanced)

If you prefer granular control:

**External .tox Only:**
1. Save component as external `.tox` to `Palette/FNStools_ext/ParHoverMIDI_VSN1.tox`
2. In each project, drag this `.tox` as an **external component** (shows reference icon)
3. Enable the `External .tox` parameter in the component
4. Good for multi-project workflows

**Custom External Repo:**
1. Disable `Auto-Create Repo` parameter
2. Create a table DAT manually at your preferred location
3. Set `Slots Repo` parameter to point to your table
4. Good for custom project structures

**Both (Recommended):**
- Combine external `.tox` + external Repo for maximum flexibility
- Best for production environments with multiple projects

## MIDI Mapping Configuration

### Default VSN1 Mapping

**Quick Setup:**
- Click `Use Defaults for VSN1` button in **Mapping** tab
- Automatically configures all MIDI mappings

**Default Configuration:**
- **MIDI Channel**: 16 (appears as 15 in Grid Editor)
- **MIDI Indices**: Correspond to element indices in grid
  - TouchDesigner: 1-indexed
  - Grid Editor: 0-indexed

### Manual Mapping

For custom configurations or non-VSN1 controllers:

**Required Steps:**

1. **Set Device ID** (CRITICAL):
   - Open component's **Mapping** tab
   - Set `Device ID` parameter
   - Find ID in TouchDesigner's MIDI Device Mapper (Dialogs → MIDI Mapper)
   - Must match your physical MIDI controller

2. **Set MIDI Channel:**
   - Default: 16 for VSN1
   - Adjust in **Mapping** tab if needed

3. **Map MIDI Indices:**
   - **Manual**: Set indices directly in custom parameters
   - **Learn Mode**: Hover over empty mapping fields and move MIDI controls
   - **Configure Steps**: Set step sizes in Mapping tab (default: 0.001, 0.01, 0.1, 1)

### Grid Editor Configuration (VSN1)

- **System element**: Defines channel as global variable `gch`
- **MIDI blocks**: Can be customized per element if needed
- See Grid Editor package documentation for details

### Learning System

The component includes automatic MIDI learning:

1. Hover over any empty Index parameter in **Mapping** tab
2. Move your MIDI knob or press button
3. Index automatically assigns
4. Works for knobs, buttons, steps, banks, and pulse controls

## Known Issues

- Screen updates can be laggy (system tries its best)
- UI color changes may cause performance impact when switching modes
- **Component limitation**: Only one instance allowed per project, and only one project open at a time

## Troubleshooting

### MIDI Not Responding

**Check:**
- Device ID set correctly in Mapping tab
- MIDI device active in TD's MIDI Device Mapper
- Using endless/relative MIDI encoders (not standard potentiometers)
- MIDI channel matches device channel

**Solution:**
- Verify Device ID matches exactly
- Test with TD's MIDI Monitor
- For VSN1: Use `Use Defaults for VSN1` to reset configuration

### VSN1 Screen Not Updating

**Check:**
- Grid Editor is open
- Grid Editor has exclusive access to port `9642`
- `VSN1 Support` parameter enabled
- WebSocket connection active

**Solution:**
- Pulse `Reset Comm` parameter
- Restart Grid Editor
- Check no other apps using port 9642
- Verify package installed correctly

### Grid Editor Won't Auto-Open

**Check:**
- Installation path matches common locations
- Grid Editor actually installed

**Solution:**
- Open Grid Editor manually
- Check installation path in component code
- Ensure proper permissions for auto-launch

### Parameters Not Adjusting

**Check:**
- Parameter mode (must be Constant or Bind)
- Not an expression parameter (expressions show `_EXPR_` error)
- Parameter type supported (Numeric, Menu, Toggle, Pulse)
- For StrMenus: `Control StrMenus` enabled or parameter in active slot

**Solution:**
- Switch parameter to Constant mode
- Check for validation error messages on screen
- Review [User Guide](user-guide.md) for supported types

### Undo Not Working

**Check:**
- `Enable Undo` parameter enabled
- Using correct keyboard shortcuts
- Operation is undoable (all parameter changes and slot operations are)

**Solution:**
- Enable `Enable Undo` in customization parameters
- Verify keyboard shortcuts match your OS

### Slots Lost After Update

**Solution:**
- Set up external storage using [Update Compatibility guide](getting-started.html#-best-practices-for-update-compatibility) before updating
- Use the "Externalize Component" button in About page
- Restore from backup if available
- Manually recreate slot assignments

### Multiple Components or Projects

**Issue:**
- Trying to use multiple component instances in one project
- Having multiple TouchDesigner projects open with the component

**Solution:**
- Only use **one component instance** per project file
- Only have **one project open** at a time with this component
- Place component at **root `/`** for best compatibility
- This limitation is due to communication and architecture constraints

## Development

### Project Structure

The codebase uses a modular architecture:

```
scripts/HoveredMidiRelative/
├── constants.py              # All constants and enums
├── validators.py             # Parameter validation logic
├── formatters.py             # Label and value formatting
├── decorators.py             # Common decorators
├── handlers.py               # MIDI message processing
├── managers/
│   ├── slot_manager.py       # Slot operations & invalidation
│   ├── display_manager.py    # Display & VSN1 hardware
│   ├── ui_manager.py         # Local UI management
│   ├── undo_manager.py       # Undo/redo system
│   └── repo_manager.py       # Persistent storage
└── HoveredMidiRelativeExt.py # Main extension class
```

### Core Components

**HoveredMidiRelativeExt**
- Main extension class
- TouchDesigner integration
- Mouse hover detection

**MidiMessageHandler**
- Processes MIDI input (steps, knobs, pulses, slots, banks)
- ParGroup support
- Type-specific handling

**DisplayManager**
- Centralizes display logic
- VSN1 hardware communication
- Batched LED updates
- UI rendering coordination

**SlotManager**
- Slot assignment/activation/clearing
- Bank switching
- Parameter invalidation/recovery
- Sequential dialog processing

**UndoManager**
- History tracking for all operations
- Parameter value changes, resets
- Slot operations
- Batch update support

**RepoManager**
- Persistent storage management
- Table-based architecture
- Bank/slot data handling

**ParameterValidator**
- Parameter compatibility validation
- ParGroup support
- Mixed valid/invalid parameter handling

**LabelFormatter**
- Smart label compression
- ParGroup detection (`>` prefix)
- Priority formatting

### Key Features

- Mouse hover detection with automatic ParGroup detection
- Full ParGroup support (control RGB, XYZ, etc. simultaneously)
- Permissive slot assignment (allows expressions/exports, skips during manipulation)
- Smart ParGroup handling:
  - Single-parameter groups treated as individuals
  - Invalid parameters skipped, not blocked
  - Type consistency validation
- Robust MIDI processing with error handling
- Centralized parameter calculations
- Smart learning system
- Multiple banks with independent management
- Bank-aware UI updates
- Optimized VSN1 communication
- Unified display architecture
- Safe handling of empty/invalid MIDI configs

### Grid Package

This repo contains the Grid package code for a monolithic repo, based on the [Intech Studio WebSocket example package](https://github.com/intechstudio/package-websocket).

**Package Structure:**
- Root contains npm package configuration
- `build.js` compiles package for Grid Editor
- Component handles WebSocket communication

### Contributing Guidelines

When contributing:

1. **Testing:**
   - Test with multiple MIDI controllers
   - Verify VSN1 integration
   - Test with/without Grid Editor
   - Validate bank switching
   - Check undo/redo functionality

2. **Compatibility:**
   - Maintain existing configuration compatibility
   - Don't break saved slot formats
   - Preserve MIDI mapping structure
   - Support both internal and external Repos

3. **Documentation:**
   - Update relevant docs (getting-started, user-guide, or advanced)
   - Add inline code comments for complex logic
   - Update README if adding major features
   - Include examples for new features

4. **Code Style:**
   - Follow existing module structure
   - Use type hints where possible
   - Add docstrings to new functions/classes
   - Keep concerns separated (validators, formatters, etc.)
  
---

[← User Guide](user-guide.html) | [Home](index.html)

