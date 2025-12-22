# ST7789 Display Overlays for Jetson Orin

Device tree overlays for configuring SPI and GPIO pins for ST7789 LCD displays on Jetson Orin platforms.

## Python Driver

For a complete Python driver that works with these overlays, see:

**[jetson-orin-st7789](https://github.com/jetsonhacks/jetson-orin-st7789)**

The Python package provides:
- High-level ST7789 display driver with PIL/Pillow integration
- Pre-configured wiring presets matching these overlays
- Examples and comprehensive test suite
- Command-line tools for demos and testing

## Overlays Provided

Three pre-configured overlays for different wiring configurations:

| Configuration | DC Pin | RST Pin | Use Case |
|---------------|--------|---------|----------|
| [jetson-default](jetson-default/) | 29 | 31 | Standard Jetson Orin wiring |
| [waveshare](waveshare/) | 13 | 22 | Waveshare 2inch LCD module |
| [adafruit](adafruit/) | 18 | 22 | Adafruit ST7789 displays |

All configurations use the same SPI pins (19, 21, 23, 24) - only DC and RST differ.

## Installation

Choose the configuration that matches your wiring:

### Jetson Default Configuration (Recommended)

Standard Jetson Orin wiring using pins 29 and 31:

```bash
cd jetson-default
sudo ./install.sh
sudo reboot
```

### Waveshare Configuration

For Waveshare 2inch LCD modules (pins 13, 22):

```bash
cd waveshare
sudo ./install.sh
sudo reboot
```

### Adafruit Configuration

For Adafruit ST7789 displays (pins 18, 22):

```bash
cd adafruit
sudo ./install.sh
sudo reboot
```

## Verification

After installing overlay and rebooting:

```bash
# Check SPI device exists
ls -l /dev/spidev1.0
# Should show: crw-rw---- 1 root gpio ...

# Verify GPIO pins configured (example for Waveshare)
sudo gpioinfo | grep -E "spi3_sck|spi3_miso"
# Pins should show as GPIO-capable

# Use pin inspector tool (from overlay-guide root)
cd ../../tools
sudo python3 pin_inspector.py 13  # DC pin
sudo python3 pin_inspector.py 22  # RST pin
# Both should show: "Pin is configured as GPIO and ready to use!"
```

## After Installing Overlay

See https://github.com/jetsonhacks/jetson-orin-st7789

## Wiring Reference

### Common SPI Pins (All Configurations)

| Signal | Jetson Pin | GPIO Function |
|--------|------------|---------------|
| 3.3V   | Pin 17     | Power |
| GND    | Pin 25     | Ground |
| MOSI   | Pin 19     | SPI1_MOSI |
| MISO   | Pin 21     | SPI1_MISO |
| SCK    | Pin 23     | SPI1_SCK |
| CS     | Pin 24     | SPI1_CS0 |

### Variable Pins (Configuration-Specific)

| Configuration | DC Pin | RST Pin | Python Preset |
|---------------|--------|---------|---------------|
| Jetson Default | Pin 29 | Pin 31 | `wiring='jetson'` |
| Waveshare | Pin 13 | Pin 22 | `wiring='waveshare'` |
| Adafruit | Pin 18 | Pin 22 | `wiring='adafruit'` |

**Important:** Your Python wiring preset must match the overlay you installed!

## Troubleshooting

### Overlay Not Loading

```bash
# Check overlay file exists
ls -l /boot/jetson-orin-st7789-*.dtbo

# Check extlinux.conf
sudo cat /boot/extlinux/extlinux.conf | grep overlays
# Should show: overlays=/boot/jetson-orin-st7789-*.dtbo

# Check for errors in boot log
dmesg | grep -i overlay
```

### SPI Device Missing

```bash
# List all SPI devices
ls -l /dev/spidev*

# If no devices, check kernel modules
lsmod | grep spi
```

### Permission Denied

```bash
# Add user to gpio and dialout groups
sudo usermod -a -G gpio,dialout $USER
# Log out and back in for changes to take effect
```

### Display Not Working

1. Verify overlay matches your wiring configuration
2. Check Python preset matches overlay
3. Verify physical wiring connections
4. Test with known-good display

For detailed troubleshooting, see the [OVERLAYS_MASTER_GUIDE.md](OVERLAYS_MASTER_GUIDE.md).

## Creating Custom Overlays

If you need a different pin configuration, see the [template directory](../template/) for creating custom overlays.

## Documentation

- Individual overlay READMEs: [jetson-default](jetson-default/README.md), [waveshare](waveshare/README.md), [adafruit](adafruit/README.md)
- [OVERLAYS_MASTER_GUIDE.md](OVERLAYS_MASTER_GUIDE.md) - Complete overlay guide
- [Device Tree Basics](../../docs/DEVICE_TREE_BASICS.md) - Understanding device trees
- [FDT Configuration](../../docs/FDT_CONFIGURATION.md) - FDT system details
- [Main README](../../README.md) - General overlay guide

## Related Projects

- [jetson-orin-st7789](https://github.com/jetsonhacks/jetson-orin-st7789) - Python driver for ST7789 displays on Jetson Orin
