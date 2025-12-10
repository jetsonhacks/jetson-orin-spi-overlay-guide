# ST7789 Display Overlays - Complete Guide

## Overview

This guide covers three device tree overlays for ST7789 displays on Jetson Orin, each supporting different pinouts:

1. **Jetson Default** - Original pinout (pins 29, 31)
2. **Waveshare** - Raspberry Pi compatible (pins 13, 22)
3. **Adafruit** - Raspberry Pi compatible (pins 18, 22)

## Quick Reference

| Configuration | DC Pin | RST Pin | BL Pin | Use When |
|---------------|--------|---------|--------|----------|
| **Jetson Default** | 29 | 31 | 17 | Custom hardware, existing projects |
| **Waveshare** | 22 | 13 | 17 | Waveshare 2inch LCD Module |
| **Adafruit** | 22 | 18 | 17 | Adafruit 2.0" 320x240 IPS TFT |

## Files Overview

### Device Tree Overlays
- `jetson-st7789-default.dts` → `jetson-st7789-default.dtbo`
- `jetson-st7789-waveshare.dts` → `jetson-st7789-waveshare.dtbo`
- `jetson-st7789-adafruit.dts` → `jetson-st7789-adafruit.dtbo`

### Installation Scripts
- `install_default_overlay.sh` - Install Jetson default configuration
- `install_waveshare_overlay.sh` - Install Waveshare configuration
- `install_adafruit_overlay.sh` - Install Adafruit configuration

### Test Scripts
- `test_jetson_default.py` - Tests pins 29, 31
- `test_waveshare_default.py` - Tests pins 13, 22
- `test_adafruit_default.py` - Tests pins 18, 22

### Documentation
- `JETSON_DEFAULT_OVERLAY_README.md` - Jetson default setup
- `WAVESHARE_OVERLAY_README.md` - Waveshare setup
- `ADAFRUIT_OVERLAY_README.md` - Adafruit setup
- `DEFAULT_CONFIGURATION.md` - Preset recommendations

### Tools
- `tools/pin_inspector.py` - Check pin configuration

## Installation Workflow

### Step 1: Choose Your Configuration

Determine which pinout matches your display:
- Follow **manufacturer's wiring diagram**
- Check what pins your display is already connected to
- Choose preset that matches your hardware

### Step 2: Run Installation Script

Choose ONE of the following:

#### For Jetson Default (pins 29, 31):
```bash
chmod +x install_default_overlay.sh
sudo ./install_default_overlay.sh
```

#### For Waveshare (pins 13, 22):
```bash
chmod +x install_waveshare_overlay.sh
sudo ./install_waveshare_overlay.sh
```

#### For Adafruit (pins 18, 22):
```bash
chmod +x install_adafruit_overlay.sh
sudo ./install_adafruit_overlay.sh
```

Each script will:
1. Check for root privileges
2. Install device-tree-compiler if needed
3. Compile the overlay (.dts → .dtbo)
4. Install to /boot/
5. Detect the correct base device tree (FDT)
6. Backup extlinux.conf with timestamp
7. Create a new boot entry with proper FDT and OVERLAYS
8. Set the new entry as default
9. Prompt for reboot

### Step 3: Reboot

When prompted, reboot your system:
```bash
# The script will offer to reboot
# Or manually:
sudo reboot
```

### Step 4: Verify Configuration

After reboot, check pins are configured:

```bash
# For Jetson Default
sudo python3 tools/pin_inspector.py 29
sudo python3 tools/pin_inspector.py 31

# For Waveshare
sudo python3 tools/pin_inspector.py 13
sudo python3 tools/pin_inspector.py 22

# For Adafruit
sudo python3 tools/pin_inspector.py 18
sudo python3 tools/pin_inspector.py 22
```

All pins should show: "✓ Pin is configured as GPIO and ready to use!"

### Step 5: Test Display

```bash
# For Jetson Default
sudo python3 test_jetson_default.py

# For Waveshare
sudo python3 test_waveshare_default.py

# For Adafruit
sudo python3 test_adafruit_default.py
```

### Step 6: Use in Code

```python
from jetson_st7789 import from_preset

# Use the preset matching your overlay
display = from_preset('jetson')      # For default
display = from_preset('waveshare')   # For Waveshare
display = from_preset('adafruit')    # For Adafruit

# Display something
display.fill((255, 0, 0))  # Red
```

## Physical Wiring

### Common Pins (All Configurations)
```
Display -> Jetson
-----------------
VCC    -> Pin 1 (3.3V)
GND    -> Pin 6 (Ground)
MOSI   -> Pin 19
CLK    -> Pin 23
CS     -> Pin 24
BL     -> Pin 17 (3.3V)
```

### Configuration-Specific Pins

**Jetson Default:**
```
DC  -> Pin 29
RST -> Pin 31
```

**Waveshare:**
```
DC  -> Pin 22
RST -> Pin 13
```

**Adafruit:**
```
DC  -> Pin 22
RST -> Pin 18
```

## Boot Configuration Details

Each installation script creates a new LABEL entry in `/boot/extlinux/extlinux.conf`:

### Jetson Default Entry:
```
LABEL JetsonDefault
	MENU LABEL ST7789 Default Config (SPI1 + GPIO 29, 31)
	LINUX /boot/Image
	FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
	INITRD /boot/initrd
	APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 ...
	OVERLAYS /boot/jetson-st7789-default.dtbo
```

### Waveshare Entry:
```
LABEL Waveshare
	MENU LABEL Waveshare ST7789 Config
	LINUX /boot/Image
	FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
	INITRD /boot/initrd
	APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 ...
	OVERLAYS /boot/jetson-st7789-waveshare.dtbo
```

### Adafruit Entry:
```
LABEL Adafruit
	MENU LABEL Adafruit ST7789 Config (SPI0)
	LINUX /boot/Image
	FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
	INITRD /boot/initrd
	APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 ...
	OVERLAYS /boot/jetson-st7789-adafruit.dtbo
```

Key elements:
- **FDT** line specifies the base device tree
- **OVERLAYS** line specifies the overlay to apply
- **APPEND** line is copied from the primary entry

## Technical Details

### SPI Configuration (Same for All)

All three overlays configure SPI1:
- Pin 19: MOSI (spi1_mosi_pz5)
- Pin 21: MISO (spi1_miso_pz4)
- Pin 23: SCLK (spi1_sck_pz3)
- Pin 24: CS0 (spi1_cs0_pz6)
- Pin 26: CS1 (spi1_cs1_pz7)

### GPIO Pin Mappings

| Physical Pin | Jetson SoC Pin | Function | Used By |
|--------------|----------------|----------|---------|
| 13 | spi3_sck_py0 | rsvd1 | Waveshare RST |
| 18 | spi3_cs0_py3 | rsvd1 | Adafruit RST |
| 22 | spi3_miso_py1 | rsvd1 | Waveshare/Adafruit DC |
| 29 | soc_gpio32_pq5 | rsvd0 | Jetson DC |
| 31 | soc_gpio33_pq6 | rsvd0 | Jetson RST |

### Pin Configuration Differences

**Jetson Default (pins 29, 31):**
- Function: `rsvd0`
- Pull: up (0x2)
- Input: disabled (output only)

**Waveshare/Adafruit (pins 13, 18, 22):**
- Function: `rsvd1`
- Pull: none (0x0)
- Input: enabled

## Switching Between Configurations

To switch between configurations:

### Method 1: Change DEFAULT in Boot Config

```bash
# Edit bootloader config
sudo nano /boot/extlinux/extlinux.conf

# Change the DEFAULT line to your desired configuration:
DEFAULT JetsonDefault   # For Jetson default
DEFAULT Waveshare       # For Waveshare
DEFAULT Adafruit        # For Adafruit

# Save and reboot
sudo reboot
```

### Method 2: Run Different Installer

```bash
# Uninstall current (optional - just changing DEFAULT is enough)
# Install different configuration
sudo ./install_waveshare_overlay.sh  # Will set Waveshare as default

# Reboot
sudo reboot
```

### After Switching:

1. **Verify pins** with pin_inspector.py
2. **Test display** with appropriate test script
3. **Update code** to use correct preset

Example:
```bash
# Currently using Jetson default, want to switch to Waveshare

# 1. Edit bootloader
sudo nano /boot/extlinux/extlinux.conf
# Change: DEFAULT JetsonDefault
# To:     DEFAULT Waveshare

# 2. Reboot
sudo reboot

# 3. Verify
sudo python3 tools/pin_inspector.py 13
sudo python3 tools/pin_inspector.py 22

# 4. Test
sudo python3 test_waveshare_default.py

# 5. Update code to use 'waveshare' preset
```

## Reverting to Original Configuration

To go back to the original Jetson configuration (no overlays):

```bash
# Edit bootloader config
sudo nano /boot/extlinux/extlinux.conf

# Change DEFAULT back to primary
DEFAULT primary

# Save and reboot
sudo reboot
```

Alternatively, restore from backup:
```bash
# List backups
ls -lt /boot/extlinux/extlinux.conf.backup.*

# Restore a backup (choose the timestamp you want)
sudo cp /boot/extlinux/extlinux.conf.backup.20241209-143022 /boot/extlinux/extlinux.conf

# Reboot
sudo reboot
```

## Troubleshooting

### Installation Script Fails

```bash
# Check if you ran with sudo
sudo ./install_waveshare_overlay.sh

# Check if .dts file exists
ls -l jetson-st7789-*.dts

# Check for compilation errors in output
# Most common: missing device-tree-compiler
sudo apt-get update
sudo apt-get install -y device-tree-compiler
```

### Overlay Doesn't Load

```bash
# Check if overlay file exists
ls -l /boot/jetson-st7789-*.dtbo

# Check bootloader config
cat /boot/extlinux/extlinux.conf | grep -A 5 "LABEL"

# Verify OVERLAYS line is present
cat /boot/extlinux/extlinux.conf | grep OVERLAYS

# Check dmesg for overlay loading messages
dmesg | grep -i overlay
dmesg | grep -i pinmux
```

### Pins Not Configured

```bash
# Verify which boot entry is active
grep "^DEFAULT" /boot/extlinux/extlinux.conf

# Rerun the installer
sudo ./install_waveshare_overlay.sh  # or whichever you're using

# Reboot
sudo reboot

# Check pins after reboot
sudo python3 tools/pin_inspector.py 13  # adjust pin number
```

### Display Not Working

```bash
# 1. Check SPI device exists
ls -l /dev/spidev0.0

# 2. Verify pin configuration
sudo python3 tools/pin_inspector.py <dc_pin>
sudo python3 tools/pin_inspector.py <rst_pin>

# 3. Check physical connections
# Use multimeter or test with --blink flag
sudo python3 tools/pin_inspector.py 13 --blink

# 4. Try slower SPI speed
python3 -c "
from jetson_st7789 import ST7789
d = ST7789(dc_pin=22, rst_pin=13, spi_speed_hz=62500000)
d.fill((255,0,0))
"

# 5. Check for conflicting overlays
cat /boot/extlinux/extlinux.conf | grep OVERLAYS
# Should only show ONE ST7789 overlay
```

### Wrong Overlay Loaded

Symptoms: Pins don't match what you expect

```bash
# Check which overlay is configured
cat /boot/extlinux/extlinux.conf | grep OVERLAYS

# Check which boot entry is default
grep "^DEFAULT" /boot/extlinux/extlinux.conf

# Verify current pin configuration
sudo python3 tools/pin_inspector.py 13
sudo python3 tools/pin_inspector.py 18
sudo python3 tools/pin_inspector.py 22
sudo python3 tools/pin_inspector.py 29
sudo python3 tools/pin_inspector.py 31
```

### Multiple Configurations Installed

Having all three installed is fine - just make sure only ONE is active:

```bash
# Check what's installed
ls -l /boot/jetson-st7789-*.dtbo

# Check what's configured (should see only ONE)
cat /boot/extlinux/extlinux.conf | grep OVERLAYS

# If multiple OVERLAYS lines, edit config to keep only one
sudo nano /boot/extlinux/extlinux.conf
```

## Best Practices

1. **One overlay at a time** - Only have one OVERLAYS line active in your boot entry
2. **Match hardware to overlay** - Use the overlay that matches your physical wiring
3. **Use automated installers** - They handle FDT detection and proper boot configuration
4. **Keep backups** - Installers automatically backup extlinux.conf with timestamps
5. **Document your choice** - Note which overlay you're using in your project
6. **Use presets in code** - Use `from_preset()` instead of hardcoding pin numbers
7. **Test after changes** - Always run pin_inspector and test scripts after modifications
8. **Verify before rebooting** - Check that bootloader config looks correct

## Success Checklist

- [ ] Chosen appropriate overlay for hardware
- [ ] Run installation script as root
- [ ] Script completed without errors
- [ ] Overlay file exists in /boot/
- [ ] Boot entry created in extlinux.conf
- [ ] FDT line present in boot entry
- [ ] OVERLAYS line present in boot entry
- [ ] Entry set as DEFAULT
- [ ] Rebooted system
- [ ] Pins verified with pin_inspector
- [ ] Test script passes
- [ ] Display shows output correctly
- [ ] Code uses correct preset

## Summary

You now have three complete, automated installation workflows:
- ✅ **Jetson Default** - For existing Jetson projects (pins 29, 31)
- ✅ **Waveshare** - For Raspberry Pi compatible Waveshare displays (pins 13, 22)
- ✅ **Adafruit** - For Raspberry Pi compatible Adafruit displays (pins 18, 22)

All three:
- Use automated installation scripts
- Properly configure FDT (base device tree)
- Create separate boot entries with OVERLAYS
- Backup existing configuration
- Include test scripts
- Have dedicated documentation
- Support preset-based initialization

Choose the one that matches your hardware and run its installer!

---

**Questions?** Check the individual README for your configuration or use `pin_inspector.py` to diagnose issues.
