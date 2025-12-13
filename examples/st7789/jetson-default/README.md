# Jetson Default ST7789 Setup for Jetson Orin

## Python Driver

After installing this overlay, use the Python driver for ST7789 displays:

**→ [jetson-orin-st7789](https://github.com/jetsonhacks/jetson-orin-st7789)**

Quick installation:
```bash
git clone https://github.com/jetsonhacks/jetson-orin-st7789.git
cd jetson-orin-st7789
uv sync

# Test with this configuration
uv run st7789-demo --wiring jetson
```

---

## Quick Start

### 1. Install Jetson Default Overlay

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
sudo python3 ../../tools/pin_inspector.py 29
sudo python3 ../../tools/pin_inspector.py 31
```

Both should show: "✓ Pin is configured as GPIO and ready to use!"

### 3. Test with Python Driver

```bash
# Install Python driver first (see Python Driver section above)
cd jetson-orin-st7789
uv run st7789-demo --wiring jetson
```

If the display shows cycling colors, your setup is working!

### 4. Use in Code

```python
from jetson_orin_st7789 import ST7789

# Direct initialization
display = ST7789(dc_pin=29, rst_pin=31)
display.fill(0xFF0000)  # Red
display.show()

# Or use preset
from jetson_orin_st7789 import from_preset

display = from_preset('jetson')
display.fill(0xFF0000)  # Red
display.show()
```

## Files

- `jetson-orin-st7789-default.dts` - Device tree overlay source
- `install.sh` - Automated installation script

## What It Configures

The overlay configures:
- **Pin 29** (soc_gpio32_pq5) as GPIO for DC (Data/Command)
- **Pin 31** (soc_gpio33_pq6) as GPIO for RST (Reset)
- **SPI1** pins (19, 21, 23, 24) for SPI communication

## Physical Wiring

```
Display Pin -> Jetson Pin
-------------------------------
VCC          -> Pin 17 (3.3V)
GND          -> Pin 25 (Ground)
MOSI         -> Pin 19 (SPI1_MOSI)
MISO         -> Pin 21 (SPI1_MISO)
CLK          -> Pin 23 (SPI1_SCK)
CS           -> Pin 24 (SPI1_CS0)
DC           -> Pin 29 (GPIO)
RST          -> Pin 31 (GPIO)
BL           -> Pin 17 (3.3V) [optional]
```

## Comparison with Other Configurations

| Configuration | DC Pin | RST Pin | Notes |
|---------------|--------|---------|-------|
| **Jetson Default** | 29 | 31 | Standard Jetson Orin wiring |
| Waveshare | 13 | 22 | Waveshare 2inch LCD module |
| Adafruit | 18 | 22 | Adafruit ST7789 displays |

All use the same SPI pins (19, 21, 23, 24).

## When to Use This Overlay

Use the Jetson default overlay when:
- You're wiring your own ST7789 display
- You prefer pins 29 and 31 for GPIO
- This is your first time setting up ST7789 on Jetson Orin
- You want the recommended default configuration

## Troubleshooting

### Overlay doesn't load
```bash
# Check if file exists
ls -l /boot/jetson-orin-st7789-default.dtbo

# Check boot config
cat /boot/extlinux/extlinux.conf | grep overlays
# Should show: overlays=/boot/jetson-orin-st7789-default.dtbo
```

### Pins not configured
```bash
# Run installer again
sudo ./install.sh

# Reboot
sudo reboot

# Check pins after reboot (from overlay-guide root)
sudo python3 ../../tools/pin_inspector.py 29
sudo python3 ../../tools/pin_inspector.py 31
```

### Display not working

1. **Verify overlay is loaded:**
   ```bash
   ls -l /boot/jetson-orin-st7789-default.dtbo
   cat /boot/extlinux/extlinux.conf | grep overlays
   ```

2. **Check SPI device exists:**
   ```bash
   ls -l /dev/spidev1.0
   # Should show: crw-rw---- 1 root gpio ...
   ```

3. **Verify GPIO pins:**
   ```bash
   sudo gpioinfo | grep -E "soc_gpio32_pq5|soc_gpio33_pq6"
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
   uv run st7789-test --wiring jetson
   ```

### Wrong Python Preset

Make sure you use `wiring='jetson'` in Python code:

```python
# CORRECT
display = ST7789(wiring='jetson')

# WRONG - will use wrong pins!
display = ST7789(wiring='waveshare')
display = ST7789(wiring='adafruit')
```

### Switching Between Configurations

If you need to switch to a different wiring configuration:

```bash
# 1. Install the other overlay
cd ../waveshare  # or ../adafruit
sudo ./install.sh

# 2. Reboot
sudo reboot

# 3. Update Python code to match
# Change wiring='jetson' to wiring='waveshare' or wiring='adafruit'
```

**Note:** Only one overlay can be active at a time. The last one installed becomes active.

## Pin Functions

The Jetson default configuration:

- **Pin 29** (soc_gpio32_pq5):
  - Function: rsvd0 (GPIO mode)
  - Pull: up (0x2)
  - Tristate: drive (0x0)
  - Direction: output

- **Pin 31** (soc_gpio33_pq6):
  - Function: rsvd0 (GPIO mode)
  - Pull: up (0x2)
  - Tristate: drive (0x0)
  - Direction: output

## Uninstalling

To remove the overlay and revert to original configuration:

```bash
# 1. Edit boot config
sudo nano /boot/extlinux/extlinux.conf

# 2. Find and remove the overlays= line
# Remove: overlays=/boot/jetson-orin-st7789-default.dtbo

# 3. Save and reboot
sudo reboot

# 4. Optional: Remove overlay file
sudo rm /boot/jetson-orin-st7789-default.dtbo
```

## Success Checklist

- [ ] `install.sh` completed successfully
- [ ] Overlay installed to `/boot/jetson-orin-st7789-default.dtbo`
- [ ] Boot config updated with overlays line
- [ ] Rebooted system
- [ ] Pin 29 shows configured as GPIO
- [ ] Pin 31 shows configured as GPIO
- [ ] `/dev/spidev1.0` exists
- [ ] User added to gpio and dialout groups
- [ ] Python driver works with `wiring='jetson'`

## Related Documentation

- [ST7789 Examples Overview](../README.md) - All ST7789 configurations
- [jetson-orin-st7789 Driver](https://github.com/jetsonhacks/jetson-orin-st7789) - Python driver
- [Device Tree Basics](../../../docs/DEVICE_TREE_BASICS.md) - Understanding overlays
- [FDT Configuration](../../../docs/FDT_CONFIGURATION.md) - Boot system details

---

**Need help?** See the [main overlay guide](../../../README.md) or open an issue on GitHub.
