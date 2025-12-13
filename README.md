# Jetson Orin SPI Device Tree Overlay Guide

**Complete guide and toolkit for configuring SPI devices on NVIDIA Jetson Orin using device tree overlays.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Driver](https://img.shields.io/badge/Python_Driver-jetson--orin--st7789-green)](https://github.com/jetsonhacks/jetson-orin-st7789)

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
- Proper bootloader setup with FDT and overlays directives

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
git clone https://github.com/jetsonhacks/jetson-orin-spi-overlay-guide.git
cd jetson-orin-spi-overlay-guide/examples/st7789

# Choose the configuration that matches your hardware:
# - jetson-default (pins 29, 31) - Recommended for custom setups
# - waveshare (pins 13, 22) - For Waveshare 2" LCD Module
# - adafruit (pins 18, 22) - For Adafruit 2.0" 320x240 IPS TFT

# Install the overlay (example: Jetson default)
cd jetson-default
chmod +x install.sh
sudo ./install.sh

# Reboot when prompted
sudo reboot

# Verify pins are configured
sudo python3 ../../tools/pin_inspector.py 29
sudo python3 ../../tools/pin_inspector.py 31
```

The installation script automatically installs the device tree compiler if needed.

### Install Python Driver

After installing the overlay, install the Python driver:

```bash
git clone https://github.com/jetsonhacks/jetson-orin-st7789.git
cd jetson-orin-st7789
uv sync

# Test with matching wiring preset
uv run st7789-demo --wiring jetson  # or waveshare, adafruit
```

## Features

### Automated Installation
- **Automatic FDT detection** - Finds the correct base device tree for your hardware
- **Bootloader configuration** - Updates boot config with overlays= directive
- **Backup management** - Timestamped backups of extlinux.conf
- **Dependency handling** - Automatically installs device tree compiler if needed
- **Error handling** - Clear messages if something goes wrong

### Multiple Configurations
- Install multiple overlays
- Switch between them by reinstalling different overlay
- Easy rollback to original configuration
- No conflicts between overlays

### Debugging Tools
- **pin_inspector.py** - Verify GPIO pin configuration
- **detect_fdt.sh** - Detect correct base device tree
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

**Python Driver:** [jetson-orin-st7789](https://github.com/jetsonhacks/jetson-orin-st7789)

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
5. **Bootloader Configuration** - Update extlinux.conf with overlays= directive
6. **Backup** - Timestamped backup of extlinux.conf
7. **Reboot** - Prompt to reboot and apply changes

### Boot Configuration Example

The installer adds an `overlays=` line to the APPEND section:

```
LABEL primary
    MENU LABEL primary kernel
    LINUX /boot/Image
    FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
    INITRD /boot/initrd
    APPEND ${cbootargs} ... overlays=/boot/jetson-orin-st7789-default.dtbo
```

## Documentation

### Core Guides
- [Device Tree Basics](docs/DEVICE_TREE_BASICS.md) - Understanding device trees
- [FDT Configuration](docs/FDT_CONFIGURATION.md) - Base device tree setup

### Example Documentation
- [ST7789 Examples Overview](examples/st7789/README.md) - All ST7789 configurations
- [ST7789 Master Guide](examples/st7789/OVERLAYS_MASTER_GUIDE.md) - Complete technical guide

## Tools

### Pin Inspector

Verify GPIO pin configuration:

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

**Note:** If checking with a multimeter with no load, you will typically measure around 1.56V.

### FDT Detector

Find the correct base device tree:

```bash
./tools/detect_fdt.sh
# Output: /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```

See [tools/README.md](tools/README.md) for complete tool documentation.

## Supported Hardware

### Tested On
- Jetson Orin Nano Developer Kit
- JetPack 6.0+

### Should Work On
- Jetson Orin NX
- Jetson AGX Orin

**Note:** The FDT detection automatically adapts to your specific hardware variant. Device tree overlays are platform-specific - overlays for Jetson Orin will not work on other Jetson platforms (Xavier, Nano, TX2) without modification.

## Switching Configurations

If you need to switch between overlays, simply install a different one:

```bash
# Switch from jetson-default to waveshare
cd examples/st7789/waveshare
sudo ./install.sh
sudo reboot
```

The installer will update the boot configuration automatically.

## Reverting Changes

### Remove Overlay

```bash
# Edit bootloader config
sudo nano /boot/extlinux/extlinux.conf

# Find and remove the overlays= parameter from APPEND line
# Before: APPEND ${cbootargs} ... overlays=/boot/jetson-orin-st7789-*.dtbo
# After:  APPEND ${cbootargs} ...

# Save and reboot
sudo reboot
```

### Restore from Backup

```bash
# List backups
ls -lt /boot/extlinux/extlinux.conf.backup.*

# Restore
sudo cp /boot/extlinux/extlinux.conf.backup.YYYYMMDD-HHMMSS \
        /boot/extlinux/extlinux.conf
sudo reboot
```

## Troubleshooting

### Overlay doesn't load
```bash
# Verify overlay file exists
ls -l /boot/jetson-orin-*.dtbo

# Check bootloader config
cat /boot/extlinux/extlinux.conf | grep overlays

# Check dmesg for errors
dmesg | grep -i overlay
```

### Pins not configured
```bash
# Run installer again
cd examples/st7789/jetson-default  # or your overlay directory
sudo ./install.sh
sudo reboot

# Verify with pin inspector
sudo python3 tools/pin_inspector.py <pin_number>
```

### Permission denied on GPIO
```bash
# Add user to gpio and dialout groups
sudo usermod -a -G gpio,dialout $USER
# Log out and back in
```

For more help, see the [OVERLAYS_MASTER_GUIDE](examples/st7789/OVERLAYS_MASTER_GUIDE.md).

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

- **[jetson-orin-st7789](https://github.com/jetsonhacks/jetson-orin-st7789)** - Python driver for ST7789 displays on Jetson Orin. Works with the overlays in this repository.
- [jetson-gpio](https://github.com/NVIDIA/jetson-gpio) - NVIDIA's GPIO library for Jetson

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Issues**: [GitHub Issues](https://github.com/jetsonhacks/jetson-orin-spi-overlay-guide/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jetsonhacks/jetson-orin-spi-overlay-guide/discussions)

## Acknowledgments

Created by JetsonHacks for the Jetson Orin community.

## Releases

### December 2025
- Initial Release
- ST7789 display examples (jetson-default, waveshare, adafruit)
- Automated installation with FDT detection
- Pin inspection and debugging tools
