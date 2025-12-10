# Jetson Orin SPI Device Tree Overlay Guide

**Complete guide and toolkit for configuring SPI devices on NVIDIA Jetson Orin using device tree overlays.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What This Repository Provides

- **Automated installation scripts** with intelligent FDT (Flattened Device Tree) detection
- **Working examples** - ST7789 display overlays with multiple pinout configurations
- **Reusable templates** for creating your own SPI device overlays
- **Comprehensive documentation** on device tree overlays for Jetson
- **Best practices** for bootloader configuration
- **Debugging tools** - Pin inspection and verification utilities

## Why This Exists

NVIDIA's official documentation on device tree overlays is minimal and scattered. This repository fills that gap by providing:

- Real, tested examples that actually work
- Automated tooling that handles the complexity
- Clear explanations of what's happening under the hood
- Multiple configuration management - switch between overlays easily
- Proper bootloader setup with FDT and OVERLAYS directives

If you've ever struggled with:
- "How do I configure SPI pins on Jetson Orin?"
- "What's the correct way to add a device tree overlay?"
- "Why isn't my overlay loading?"
- "How do I find the right FDT file?"

...then this repository is for you!

## Quick Start

### Example: ST7789 Display Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/jetson-orin-spi-overlay-guide.git
cd jetson-orin-spi-overlay-guide/examples/st7789

# Choose the configuration that matches your hardware:
# - Jetson default (pins 29, 31) - Recommended for custom setups
# - Waveshare (pins 13, 22) - For Waveshare 2" LCD Module
# - Adafruit (pins 18, 22) - For Adafruit 2.0" 320x240 IPS TFT

# Install the overlay (example: Waveshare)
chmod +x install_default_overlay.sh
sudo ./install_default_overlay.sh

# Reboot when prompted
sudo reboot

# Verify pins are configured
sudo python3 ../../tools/pin_inspector.py 29
sudo python3 ../../tools/pin_inspector.py 31
```

The installation script automatically installs the device tree compiler if needed.

## Features

### Automated Installation
- **Automatic FDT detection** - Finds the correct base device tree for your hardware
- **Bootloader configuration** - Creates proper boot entries with FDT and OVERLAYS
- **Backup management** - Timestamped backups of extlinux.conf
- **Dependency handling** - Automatically installs device tree compiler if needed
- **Error handling** - Clear messages if something goes wrong

### Multiple Configurations
- Install multiple overlays
- Switch between them by changing boot default
- Easy rollback to original configuration
- No conflicts between overlays

### Debugging Tools
- **pin_inspector.py** - Verify GPIO pin configuration
- Blink test mode for hardware verification
- Detailed error messages

### Documentation
- Complete guides for each example
- Step-by-step troubleshooting
- Technical details explained clearly

## Examples

### ST7789 Display

Complete implementation with three overlay configurations:

| Configuration | DC Pin | RST Pin | Use Case |
|---------------|--------|---------|----------|
| **Jetson Default** | 29 | 31 | Custom hardware, native Jetson pinout |
| **Waveshare** | 22 | 13 | Waveshare 2" LCD Module (RPi compatible) |
| **Adafruit** | 22 | 18 | Adafruit 2.0" IPS TFT (RPi compatible) |

Each configuration includes:
- Device tree overlay source (.dts)
- Automated installation script
- Complete documentation
- Test scripts

See [examples/st7789/](examples/st7789/) for full details.

### Create Your Own

Use the template in [examples/template/](examples/template/) to create overlays for your SPI devices:

```bash
cd examples/template
# Copy and modify the template for your device
cp device-overlay-template.dts my-device.dts
# Edit to match your hardware
nano my-device.dts
# Use the installer template
cp install_overlay_template.sh install_my_device.sh
# Customize and run
nano install_my_device.sh
chmod +x install_my_device.sh
sudo ./install_my_device.sh
```

## How It Works

### Device Tree Overlays

Device tree overlays modify the base device tree to configure hardware. For SPI devices, this typically involves:

1. **Configuring GPIO pins** - Set pins to GPIO mode for control signals (DC, RST, etc.)
2. **Configuring SPI pins** - Enable SPI bus with correct pinmux settings
3. **Setting pin properties** - Pull-up/down, drive strength, input/output mode

### Installation Process

The automated installer scripts handle:

1. **Dependency Check** - Installs device-tree-compiler if not present
2. **Compilation** - Convert .dts source to .dtbo binary
3. **Installation** - Copy overlay to /boot/
4. **FDT Detection** - Find the correct base device tree for your hardware
5. **Bootloader Configuration** - Create proper boot entry with:
   - `FDT` line pointing to base device tree
   - `OVERLAYS` line pointing to your overlay
   - Correct APPEND line from primary entry
6. **Backup** - Timestamped backup of extlinux.conf
7. **Reboot** - Prompt to reboot and apply changes

### Boot Configuration Example

```
LABEL MyDevice
    MENU LABEL My SPI Device Config
    LINUX /boot/Image
    FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
    INITRD /boot/initrd
    APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 ...
    OVERLAYS /boot/my-device.dtbo
```

## Documentation

### Core Guides
- [Device Tree Basics](docs/DEVICE_TREE_BASICS.md) - Understanding device trees
- [FDT Configuration](docs/FDT_CONFIGURATION.md) - Base device tree setup
- [Bootloader Setup](docs/BOOTLOADER_SETUP.md) - Extlinux configuration
- [Pin Configuration](docs/PIN_CONFIGURATION.md) - GPIO and pinmux
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

### Example Documentation
- [ST7789 Master Guide](examples/st7789/docs/OVERLAYS_MASTER_GUIDE.md) - Complete ST7789 documentation
- [Default Configuration](examples/st7789/docs/DEFAULT_CONFIGURATION.md) - Preset recommendations

## Tools

### Pin Inspector

Verify GPIO pin configuration. If checking with a multimeter, you will probably get a ready of ~ 1.56V as there is no load. For the default example:

```bash
# Check if a pin is configured as GPIO
sudo python3 tools/pin_inspector.py 29

# Test with blinking (hardware verification)
sudo python3 tools/pin_inspector.py 29 --blink
```

Output:
```
Pin 29 Information:
Pin is configured as GPIO and ready to use!

Physical Pin: 29
Chip: gpiochip0
Line: 106
Direction: out
```

### FDT Detector

Find the correct base device tree:

```bash
./tools/detect_fdt.sh
# Output: /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```

## Supported Hardware

### Tested On
- Jetson Orin Nano Developer Kit

### Should Work On
- Jetson Orin NX
- Jetson AGX Orin

**Note:** The FDT detection automatically adapts to your specific hardware variant.

## Switching Configurations

If you have multiple overlays installed, switch between them:

```bash
# Edit bootloader config
sudo nano /boot/extlinux/extlinux.conf

# Change the DEFAULT line:
DEFAULT MyDevice1  # or MyDevice2, or primary

# Reboot
sudo reboot
```

## Reverting Changes

### Method 1: Change Boot Default
```bash
sudo nano /boot/extlinux/extlinux.conf
# Change: DEFAULT MyDevice
# To:     DEFAULT primary
sudo reboot
```

### Method 2: Restore from Backup
```bash
# List backups
ls -lt /boot/extlinux/extlinux.conf.backup.*

# Restore
sudo cp /boot/extlinux/extlinux.conf.backup.20241209-143022 \
        /boot/extlinux/extlinux.conf
sudo reboot
```

## Troubleshooting

### Overlay doesn't load
```bash
# Verify overlay file exists
ls -l /boot/*.dtbo

# Check bootloader config
cat /boot/extlinux/extlinux.conf | grep OVERLAYS

# Check dmesg for errors
dmesg | grep -i overlay
```

### Pins not configured
```bash
# Run installer again
sudo ./install_my_overlay.sh

# Verify with pin inspector
sudo python3 tools/pin_inspector.py <pin_number>
```

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for complete troubleshooting guide.

## Contributing

Contributions are welcome! Here's how you can help:

### Add a New Device Example
1. Create a new directory in `examples/`
2. Include .dts file, installer script, and documentation
3. Test thoroughly on real hardware
4. Submit a pull request

### Improve Documentation
- Fix typos or clarify explanations
- Add diagrams or visual aids
- Expand troubleshooting guides

### Report Issues
- Hardware compatibility reports
- Bug reports with logs
- Feature requests

## Related Projects

- [jetson-st7789](https://github.com/yourusername/jetson-st7789) - Python driver for ST7789 displays on Jetson
- [jetson-gpio](https://github.com/NVIDIA/jetson-gpio) - NVIDIA's GPIO library for Jetson

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/jetson-orin-spi-overlay-guide/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/jetson-orin-spi-overlay-guide/discussions)

## Releases
### December, 2025
* Initial Release

