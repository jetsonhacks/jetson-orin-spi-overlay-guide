# Tools Directory

Diagnostic and utility tools for device tree overlay development on Jetson Orin.

## Available Tools

### pin_inspector.py

Comprehensive GPIO pin diagnostic tool for NVIDIA Jetson platforms.

**Quick Start:**
```bash
# Check if pin 29 is configured for GPIO
sudo python3 pin_inspector.py 29

# Check pin 31
sudo python3 pin_inspector.py 31

# Test pin with blink
sudo python3 pin_inspector.py 29 --blink
```

**Use Cases:**
- Verify GPIO configuration after installing overlay
- Troubleshoot "GPIO not working" issues
- Generate device tree overlay fragments for reference
- Test GPIO pins with visual blink test
- Debug hardware connections

**Common Pins for ST7789:**
- Pin 13: Waveshare RST
- Pin 18: Adafruit RST
- Pin 22: Waveshare/Adafruit DC
- Pin 29: Jetson default DC
- Pin 31: Jetson default RST

**Requirements:**
- Root/sudo access
- Kernel debugfs mounted
- Optional: libgpiod for blink tests ( $ sudo apt install libgpiod )

### detect_fdt.sh

Automatically detects the correct base device tree (FDT) file for your Jetson Orin.

**Quick Start:**
```bash
# Detect FDT
./detect_fdt.sh

# Use in scripts
FDT=$(./detect_fdt.sh)
echo "Base device tree: $FDT"
```

**Use Cases:**
- Automatic FDT detection in installation scripts
- Verifying which device tree your system uses
- Troubleshooting boot configuration issues

**Output Example:**
```
/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```

### compile_install_dtbo.sh

Utility script for compiling and installing device tree overlays manually.

**Quick Start:**
```bash
# Compile and install an overlay
sudo ./compile_install_dtbo.sh path/to/overlay.dts
```

**Use Cases:**
- Manual overlay compilation
- Testing overlay files before creating automated installer
- Advanced users who want control over the process

**Note:** Most users should use the automated `install.sh` scripts in each overlay directory instead. Those scripts handle both compilation AND boot configuration.

**What it does:**
1. Checks for device-tree-compiler (installs if needed)
2. Compiles .dts to .dtbo
3. Installs to /boot/
4. Verifies installation
5. Shows next steps for boot configuration

**What it does NOT do:**
- Does not update boot configuration (you must edit extlinux.conf manually)
- Does not create backup of boot config
- Does not reboot

## Common Workflows

### Verifying Overlay Installation

After installing an overlay, verify pins are configured:

```bash
# For Jetson default overlay (pins 29, 31)
sudo python3 pin_inspector.py 29
sudo python3 pin_inspector.py 31

# For Waveshare overlay (pins 13, 22)
sudo python3 pin_inspector.py 13
sudo python3 pin_inspector.py 22

# For Adafruit overlay (pins 18, 22)
sudo python3 pin_inspector.py 18
sudo python3 pin_inspector.py 22

# All should show: "Pin is configured as GPIO and ready to use!"
```

### Quick Pin Check Script

```bash
#!/bin/bash
# check_st7789_pins.sh - Check ST7789 GPIO pins

echo "Checking ST7789 display pins..."

# Choose pins based on your configuration
DC_PIN=29   # Change to 22 for Waveshare/Adafruit
RST_PIN=31  # Change to 13 for Waveshare, 18 for Adafruit

for pin in $DC_PIN $RST_PIN; do
    echo "=== Pin $pin ==="
    sudo python3 tools/pin_inspector.py $pin | grep -E "Pin is|ERROR"
done
```

### Manual Overlay Testing

If you're developing a custom overlay:

```bash
# 1. Compile and install
sudo ./compile_install_dtbo.sh my-custom-overlay.dts

# 2. Manually edit boot config
sudo nano /boot/extlinux/extlinux.conf
# Add: overlays=/boot/my-custom-overlay.dtbo

# 3. Reboot
sudo reboot

# 4. Verify pins
sudo python3 pin_inspector.py <your_pin_number>
```

## Tool Outputs

### pin_inspector.py Success
```
Pin 29 (BOARD numbering)
Physical Pin: 29
Status: READY
Pin is configured as GPIO and ready to use!
```

### pin_inspector.py Failure
```
Pin 29 (BOARD numbering)
Physical Pin: 29
Status: NOT READY
ERROR: Pin is not configured as GPIO
```

### detect_fdt.sh
```
/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```

### compile_install_dtbo.sh
```
================================================================
  Device Tree Overlay Compiler & Installer
================================================================

DTS file: jetson-orin-st7789-waveshare.dts
DTBO file: jetson-orin-st7789-waveshare.dtbo

SUCCESS: Compiled successfully
Output size: 1234 bytes
SUCCESS: Installed to /boot/jetson-orin-st7789-waveshare.dtbo

Next steps:
1. Edit /boot/extlinux/extlinux.conf
2. Add to APPEND line: overlays=/boot/jetson-orin-st7789-waveshare.dtbo
3. Reboot
```

## Related Documentation

- [Device Tree Basics](../docs/DEVICE_TREE_BASICS.md) - Understanding device trees
- [FDT Configuration](../docs/FDT_CONFIGURATION.md) - Boot system details
- [ST7789 Examples](../examples/st7789/) - Complete overlay examples with automated installers

## Notes

**For most users:** Use the automated `install.sh` scripts in the overlay directories. These tools are for advanced usage and troubleshooting.

**For developers:** These tools are building blocks for creating automated installation scripts and debugging overlay issues.
