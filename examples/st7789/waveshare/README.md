# Waveshare ST7789 Setup for Jetson Orin

## Python Driver

After installing this overlay, use the Python driver for ST7789 displays:

**→ [jetson-orin-st7789](https://github.com/jetsonhacks/jetson-orin-st7789)**

Quick installation:
```bash
git clone https://github.com/jetsonhacks/jetson-orin-st7789.git
cd jetson-orin-st7789
uv sync

# Test with this configuration
uv run st7789-demo --wiring waveshare
```

---

## Quick Start

### 1. Install Waveshare Overlay

```bash
chmod +x install.sh
sudo ./install.sh
```

The script will:
- Compile the device tree overlay
- Install it to /boot/
- Update boot configuration
- Prompt for reboot

### 2. Verify Pins

After reboot:

```bash
# From overlay-guide root directory
sudo python3 ../../tools/pin_inspector.py 13
sudo python3 ../../tools/pin_inspector.py 22
```

Both should show: "✓ Pin is configured as GPIO and ready to use!"

### 3. Test with Python Driver

```bash
# Install Python driver first (see Python Driver section above)
cd jetson-orin-st7789
uv run st7789-demo --wiring waveshare
```

If the display shows cycling colors, your setup is working!

### 4. Use in Code

```python
from jetson_orin_st7789 import ST7789

# Direct initialization
display = ST7789(dc_pin=22, rst_pin=13)
display.fill(0x0000FF)  # Blue
display.show()

# Or use preset
from jetson_orin_st7789 import from_preset

display = from_preset('waveshare')
display.fill(0x0000FF)  # Blue
display.show()
```

## Files

- `jetson-orin-st7789-waveshare.dts` - Device tree overlay source
- `install.sh` - Automated installation script

## What It Configures

The overlay configures:
- **Pin 13** (spi3_sck_py0) as GPIO for RST (Reset)
- **Pin 22** (spi3_miso_py1) as GPIO for DC (Data/Command)
- **SPI1** pins (19, 21, 23, 24) for SPI communication

## Physical Wiring

```
Waveshare Pin -> Jetson Pin
-------------------------------
VCC          -> Pin 17 (3.3V)
GND          -> Pin 25 (Ground)
DIN (MOSI)   -> Pin 19 (SPI1_MOSI)
CLK          -> Pin 23 (SPI1_SCK)
CS           -> Pin 24 (SPI1_CS0)
DC           -> Pin 22 (GPIO)
RST          -> Pin 13 (GPIO)
BL           -> Pin 17 (3.3V) [optional]
```

## Comparison with Other Configurations

| Configuration | DC Pin | RST Pin | Notes |
|---------------|--------|---------|-------|
| Jetson Default | 29 | 31 | Standard Jetson Orin wiring |
| **Waveshare** | 22 | 13 | Waveshare 2inch LCD module |
| Adafruit | 22 | 18 | Adafruit ST7789 displays |

All use the same SPI pins (19, 21, 23, 24).

## When to Use This Overlay

Use the Waveshare overlay when:
- You have a Waveshare 2inch LCD Module (ST7789V driver)
- Your display is already wired according to Waveshare's documentation
- You're following Waveshare tutorials designed for Raspberry Pi
- Your display uses pins 13 and 22 for RST and DC

## Troubleshooting

### Overlay doesn't load
```bash
# Check if file exists
ls -l /boot/jetson-orin-st7789-waveshare.dtbo

# Check boot config
cat /boot/extlinux/extlinux.conf | grep overlays
# Should show: overlays=/boot/jetson-orin-st7789-waveshare.dtbo
```

### Pins not configured
```bash
# Run installer again
sudo ./install.sh

# Reboot
sudo reboot

# Check pins after reboot (from overlay-guide root)
sudo python3 ../../tools/pin_inspector.py 13
sudo python3 ../../tools/pin_inspector.py 22
```

### Display not working

1. **Verify overlay is loaded:**
   ```bash
   ls -l /boot/jetson-orin-st7789-waveshare.dtbo
   cat /boot/extlinux/extlinux.conf | grep overlays
   ```

2. **Check SPI device exists:**
   ```bash
   ls -l /dev/spidev1.0
   # Should show: crw-rw---- 1 root gpio ...
   ```

3. **Verify GPIO pins:**
   ```bash
   sudo gpioinfo | grep -E "spi3_sck_py0|spi3_miso_py1"
   # Both should show as GPIO
   ```

4. **Check permissions:**
   ```bash
   # Add user to gpio group
   sudo usermod -a -G gpio,dialout $USER
   # Log out and back in
   ```

5. **Test with Python driver:**
   ```bash
   cd jetson-orin-st7789
   uv run st7789-test --wiring waveshare
   ```

### Wrong Python Preset

Make sure you use `wiring='waveshare'` in Python code:

```python
# CORRECT
display = ST7789(wiring='waveshare')

# WRONG - will use wrong pins!
display = ST7789(wiring='jetson')
display = ST7789(wiring='adafruit')
```

### Switching Between Configurations

If you need to switch to a different wiring configuration:

```bash
# 1. Install the other overlay
cd ../jetson-default  # or ../adafruit
sudo ./install.sh

# 2. Reboot
sudo reboot

# 3. Update Python code to match
# Change wiring='waveshare' to wiring='jetson' or wiring='adafruit'
```

**Note:** Only one overlay can be active at a time. The last one installed becomes active.

## Pin Functions

The Waveshare configuration:

- **Pin 13** (spi3_sck_py0):
  - Function: rsvd1 (GPIO mode)
  - Pull: none (0x0)
  - Tristate: drive (0x0)
  - Input: enabled (0x1)
  - Direction: output

- **Pin 22** (spi3_miso_py1):
  - Function: rsvd1 (GPIO mode)
  - Pull: none (0x0)
  - Tristate: drive (0x0)
  - Input: enabled (0x1)
  - Direction: output

## Uninstalling

To remove the overlay and revert to original configuration:

```bash
# 1. Edit boot config
sudo nano /boot/extlinux/extlinux.conf

# 2. Find and remove the overlays= line
# Remove: overlays=/boot/jetson-orin-st7789-waveshare.dtbo

# 3. Save and reboot
sudo reboot

# 4. Optional: Remove overlay file
sudo rm /boot/jetson-orin-st7789-waveshare.dtbo
```

## Success Checklist

- [ ] `install.sh` completed successfully
- [ ] Overlay installed to `/boot/jetson-orin-st7789-waveshare.dtbo`
- [ ] Boot config updated with overlays line
- [ ] Rebooted system
- [ ] Pin 13 shows configured as GPIO
- [ ] Pin 22 shows configured as GPIO
- [ ] `/dev/spidev1.0` exists
- [ ] User added to gpio and dialout groups
- [ ] Python driver works with `wiring='waveshare'`

## Related Documentation

- [ST7789 Examples Overview](../README.md) - All ST7789 configurations
- [jetson-orin-st7789 Driver](https://github.com/jetsonhacks/jetson-orin-st7789) - Python driver
- [Device Tree Basics](../../../docs/DEVICE_TREE_BASICS.md) - Understanding overlays
- [FDT Configuration](../../../docs/FDT_CONFIGURATION.md) - Boot system details

---

**Need help?** See the [main overlay guide](../../../README.md) or open an issue on GitHub.
