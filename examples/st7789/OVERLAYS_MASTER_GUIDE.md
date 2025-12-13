# ST7789 Display Overlays - Complete Guide

## Overview

This guide covers three device tree overlays for ST7789 displays on Jetson Orin, each supporting different pinouts:

1. **Jetson Default** - Standard Jetson Orin wiring (pins 29, 31)
2. **Waveshare** - Waveshare 2inch LCD module (pins 13, 22)
3. **Adafruit** - Adafruit ST7789 displays (pins 18, 22)

## Quick Reference

| Configuration | DC Pin | RST Pin | Use When |
|---------------|--------|---------|----------|
| **Jetson Default** | 29 | 31 | Custom hardware, standard wiring |
| **Waveshare** | 22 | 13 | Waveshare 2inch LCD Module |
| **Adafruit** | 22 | 18 | Adafruit 2.0" 320x240 IPS TFT |

## Files Overview

### Device Tree Overlays
- `jetson-orin-st7789-default.dts` → `jetson-orin-st7789-default.dtbo`
- `jetson-orin-st7789-waveshare.dts` → `jetson-orin-st7789-waveshare.dtbo`
- `jetson-orin-st7789-adafruit.dts` → `jetson-orin-st7789-adafruit.dtbo`

### Installation Scripts
- `jetson-default/install.sh` - Install Jetson default configuration
- `waveshare/install.sh` - Install Waveshare configuration
- `adafruit/install.sh` - Install Adafruit configuration

### Documentation
- `jetson-default/README.md` - Jetson default setup
- `waveshare/README.md` - Waveshare setup
- `adafruit/README.md` - Adafruit setup
- `README.md` - ST7789 examples overview

## Installation Workflow

### Step 1: Choose Your Configuration

Determine which pinout matches your display:
- Follow manufacturer's wiring diagram
- Check what pins your display is already connected to
- Choose overlay that matches your hardware

### Step 2: Navigate to Configuration Directory

```bash
cd examples/st7789/jetson-default   # For Jetson default
cd examples/st7789/waveshare        # For Waveshare
cd examples/st7789/adafruit         # For Adafruit
```

### Step 3: Run Installation Script

```bash
chmod +x install.sh
sudo ./install.sh
```

The script will:
1. Check for root privileges
2. Install device-tree-compiler if needed
3. Compile the overlay (.dts → .dtbo)
4. Install to /boot/
5. Detect the correct base device tree (FDT)
6. Backup extlinux.conf with timestamp
7. Update boot configuration
8. Prompt for reboot

### Step 4: Reboot

When prompted, reboot your system:
```bash
sudo reboot
```

### Step 5: Verify Configuration

After reboot, check pins are configured:

```bash
# From overlay-guide root directory
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

All pins should show: "Pin is configured as GPIO and ready to use!"

### Step 6: Install Python Driver

```bash
git clone https://github.com/jetsonhacks/jetson-orin-st7789.git
cd jetson-orin-st7789
uv sync
```

### Step 7: Test Display

```bash
# Use the wiring preset matching your overlay
uv run st7789-demo --wiring jetson      # For jetson-default
uv run st7789-demo --wiring waveshare   # For waveshare
uv run st7789-demo --wiring adafruit    # For adafruit
```

## Physical Wiring

### Common Pins (All Configurations)
```
Display -> Jetson
-----------------
VCC    -> Pin 17 (3.3V)
GND    -> Pin 25 (Ground)
MOSI   -> Pin 19 (SPI1_MOSI)
MISO   -> Pin 21 (SPI1_MISO)
CLK    -> Pin 23 (SPI1_SCK)
CS     -> Pin 24 (SPI1_CS0)
BL     -> Pin 17 (3.3V) [optional]
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

Each installation script updates `/boot/extlinux/extlinux.conf` by adding an `overlays=` line to the APPEND section.

Example configuration:
```
LABEL primary
    MENU LABEL primary kernel
    LINUX /boot/Image
    FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
    INITRD /boot/initrd
    APPEND ${cbootargs} ... overlays=/boot/jetson-orin-st7789-waveshare.dtbo
```

Key elements:
- **FDT** line specifies the base device tree
- **overlays=** in APPEND line specifies the overlay to apply

## Technical Details

### SPI Configuration (Same for All)

All three overlays configure SPI1:
- Pin 19: MOSI (spi1_mosi_pz5)
- Pin 21: MISO (spi1_miso_pz4)
- Pin 23: SCLK (spi1_sck_pz3)
- Pin 24: CS0 (spi1_cs0_pz6)

This creates `/dev/spidev1.0` for communication.

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

To switch between configurations, simply install a different overlay:

```bash
# Switch from Waveshare to Jetson default
cd examples/st7789/jetson-default
sudo ./install.sh
sudo reboot

# Update Python code to use matching preset
# Change: wiring='waveshare'
# To:     wiring='jetson'
```

The installer will update the boot configuration automatically.

## Reverting to Original Configuration

To remove the overlay and go back to original configuration:

```bash
# Edit boot config
sudo nano /boot/extlinux/extlinux.conf

# Find the APPEND line and remove the overlays= parameter
# Before: APPEND ${cbootargs} ... overlays=/boot/jetson-orin-st7789-*.dtbo
# After:  APPEND ${cbootargs} ...

# Save and reboot
sudo reboot
```

Alternatively, restore from backup:
```bash
# List backups
ls -lt /boot/extlinux/extlinux.conf.backup.*

# Restore a backup
sudo cp /boot/extlinux/extlinux.conf.backup.YYYYMMDD-HHMMSS /boot/extlinux/extlinux.conf
sudo reboot
```

## Troubleshooting

### Installation Script Fails

```bash
# Check if you ran with sudo
sudo ./install.sh

# Check if .dts file exists in current directory
ls -l *.dts

# Check for compilation errors in output
# Most common: missing device-tree-compiler
sudo apt-get update
sudo apt-get install -y device-tree-compiler
```

### Overlay Doesn't Load

```bash
# Check if overlay file exists
ls -l /boot/jetson-orin-st7789-*.dtbo

# Check boot configuration
cat /boot/extlinux/extlinux.conf | grep overlays

# Check dmesg for overlay loading messages
dmesg | grep -i overlay
dmesg | grep -i pinmux
```

### Pins Not Configured

```bash
# Verify boot config has overlays= line
cat /boot/extlinux/extlinux.conf | grep overlays

# Rerun the installer
cd examples/st7789/waveshare  # or whichever you're using
sudo ./install.sh
sudo reboot

# Check pins after reboot (from overlay-guide root)
sudo python3 tools/pin_inspector.py 13  # adjust pin number
```

### Display Not Working

```bash
# 1. Check SPI device exists
ls -l /dev/spidev1.0

# 2. Verify pin configuration
sudo python3 tools/pin_inspector.py <dc_pin>
sudo python3 tools/pin_inspector.py <rst_pin>

# 3. Check permissions
sudo usermod -a -G gpio,dialout $USER
# Log out and back in

# 4. Verify Python preset matches overlay
# If you installed waveshare overlay, use wiring='waveshare' in Python

# 5. Test with Python driver
cd jetson-orin-st7789
uv run st7789-test --wiring waveshare  # or jetson, adafruit
```

### Wrong Overlay Loaded

Symptoms: Pins don't match what you expect

```bash
# Check which overlay is configured
cat /boot/extlinux/extlinux.conf | grep overlays

# Verify current pin configuration
sudo python3 tools/pin_inspector.py 13
sudo python3 tools/pin_inspector.py 18
sudo python3 tools/pin_inspector.py 22
sudo python3 tools/pin_inspector.py 29
sudo python3 tools/pin_inspector.py 31
```

## Best Practices

1. **One overlay at a time** - Only have one overlays= line in boot config
2. **Match hardware to overlay** - Use the overlay that matches your physical wiring
3. **Use automated installers** - They handle FDT detection and proper boot configuration
4. **Keep backups** - Installers automatically backup extlinux.conf with timestamps
5. **Document your choice** - Note which overlay you're using in your project
6. **Match Python preset** - Use matching wiring preset in Python code
7. **Test after changes** - Always run pin_inspector after modifications
8. **Verify before rebooting** - Check that bootloader config looks correct

## Success Checklist

- [ ] Chosen appropriate overlay for hardware
- [ ] Run installation script as root
- [ ] Script completed without errors
- [ ] Overlay file exists in /boot/
- [ ] Boot config shows overlays= line
- [ ] Rebooted system
- [ ] Pins verified with pin_inspector
- [ ] SPI device /dev/spidev1.0 exists
- [ ] User added to gpio and dialout groups
- [ ] Python driver installed
- [ ] Python wiring preset matches overlay
- [ ] Display shows output correctly

## Python Integration

After installing an overlay, use the matching preset in Python:

```python
from jetson_orin_st7789 import ST7789

# Match your overlay choice:
display = ST7789(wiring='jetson')      # For jetson-default overlay
display = ST7789(wiring='waveshare')   # For waveshare overlay
display = ST7789(wiring='adafruit')    # For adafruit overlay

# Display something
display.fill(0xFF0000)  # Red
display.show()
```

For complete Python driver documentation, see:
[jetson-orin-st7789](https://github.com/jetsonhacks/jetson-orin-st7789)

## Summary

You now have three complete, automated installation workflows:
- Jetson Default - For standard Jetson Orin wiring (pins 29, 31)
- Waveshare - For Waveshare 2inch LCD module (pins 13, 22)
- Adafruit - For Adafruit ST7789 displays (pins 18, 22)

All three:
- Use automated installation scripts
- Properly configure FDT (base device tree)
- Update boot configuration with overlays=
- Backup existing configuration
- Have dedicated documentation
- Support Python driver integration

Choose the one that matches your hardware and run its installer!

---

**Questions?** Check the individual README for your configuration or use `pin_inspector.py` to diagnose issues.
