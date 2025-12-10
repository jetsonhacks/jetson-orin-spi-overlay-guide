# Jetson Default ST7789 Setup for Jetson Orin

## Quick Start

### 1. Install Jetson Default Overlay

```bash
chmod +x install_default_overlay.sh
sudo ./install_default_overlay.sh
```

The script will:
- Compile the device tree overlay
- Install it to /boot/
- Create a new boot entry
- Set it as default
- Prompt for reboot

### 2. Verify Pins

After reboot:

```bash
sudo python3 tools/pin_inspector.py 29
sudo python3 tools/pin_inspector.py 31
```

Both should show: "✓ Pin is configured as GPIO and ready to use!"

### 3. Test Jetson Default Display

```bash
sudo python3 test_jetson_default.py
```

If this passes, your display is working!

### 4. Use in Code

```python
from jetson_st7789 import ST7789

# Direct initialization
display = ST7789(dc_pin=29, rst_pin=31)
display.fill((255, 0, 0))  # Red

# Or use preset
from jetson_st7789 import from_preset

with from_preset('jetson') as display:
    display.fill((255, 0, 0))  # Red
```

## Files

- `jetson-st7789-default.dts` - Device tree overlay source
- `install_default_overlay.sh` - Automated installation script
- `test_jetson_default.py` - Test script

## What It Configures

The overlay configures:
- **Pin 29** (soc_gpio32_pq5) as GPIO for DC
- **Pin 31** (soc_gpio33_pq6) as GPIO for RST
- **SPI1** pins (19, 21, 23, 24, 26) for SPI communication

## Physical Wiring

```
Display Pin -> Jetson Pin
-------------------------------
VCC          -> Pin 1 (3.3V)
GND          -> Pin 6 (Ground)
MOSI         -> Pin 19 (MOSI)
CLK          -> Pin 23 (SCLK)
CS           -> Pin 24 (CE0)
DC           -> Pin 29 (GPIO)
RST          -> Pin 31 (GPIO)
BL           -> Pin 17 (3.3V)
```

## Boot Configuration

The installer creates a new boot entry in `/boot/extlinux/extlinux.conf`:

```
LABEL JetsonDefault
	MENU LABEL ST7789 Default Config (SPI1 + GPIO 29, 31)
	LINUX /boot/Image
	FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
	INITRD /boot/initrd
	APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 ...
	OVERLAYS /boot/jetson-st7789-default.dtbo
```

To revert to original configuration:
```bash
sudo nano /boot/extlinux/extlinux.conf
# Change: DEFAULT JetsonDefault
# To:     DEFAULT primary
sudo reboot
```

## Comparison with Other Configurations

| Configuration | DC Pin | RST Pin | BL Pin | Notes |
|---------------|--------|---------|--------|-------|
| **Jetson Default** | 29 | 31 | 17 | Original Jetson pinout |
| Waveshare | 22 | 13 | 17 | Raspberry Pi compatible |
| Adafruit | 22 | 18 | 17 | Raspberry Pi compatible |

## When to Use This Overlay

Use the Jetson default overlay when:
- You have existing hardware wired to pins 29 and 31
- You're creating a custom display configuration
- You prefer the original Jetson pinout over RPi compatibility
- Pins 29 and 31 are more convenient for your project

## Troubleshooting

### Overlay doesn't load
```bash
# Check if file exists
ls -l /boot/jetson-st7789-default.dtbo

# Check boot config
cat /boot/extlinux/extlinux.conf | grep -A 5 "LABEL JetsonDefault"

# Verify overlay is in boot entry
cat /boot/extlinux/extlinux.conf | grep OVERLAYS
```

### Pins not configured
```bash
# Run installer again
sudo ./install_default_overlay.sh

# Reboot
sudo reboot

# Check pins after reboot
sudo python3 tools/pin_inspector.py 29
sudo python3 tools/pin_inspector.py 31
```

### Display not working
```bash
# Check SPI device exists
ls -l /dev/spidev0.0

# Verify physical connections
sudo python3 tools/pin_inspector.py 29 --blink
sudo python3 tools/pin_inspector.py 31 --blink

# Test with slower SPI speed
python3 -c "
from jetson_st7789 import ST7789
d = ST7789(dc_pin=29, rst_pin=31, spi_speed_hz=62500000)
d.fill((255,0,0))
"
```

### Wrong boot entry active
```bash
# Check which entry is default
grep "^DEFAULT" /boot/extlinux/extlinux.conf

# Should show: DEFAULT JetsonDefault
# If not, edit and change to JetsonDefault
sudo nano /boot/extlinux/extlinux.conf
```

### Multiple Overlays

You can have all three overlays installed, but only load one at a time:

```bash
# Install all three (if needed)
sudo ./install_default_overlay.sh
sudo ./install_waveshare_overlay.sh
sudo ./install_adafruit_overlay.sh

# Switch between them by changing DEFAULT in extlinux.conf:
sudo nano /boot/extlinux/extlinux.conf

# Set DEFAULT to one of:
# - DEFAULT JetsonDefault
# - DEFAULT Waveshare
# - DEFAULT Adafruit

sudo reboot
```

**Note:** All three overlays configure the same SPI pins, so they're mutually exclusive. Choose the one that matches your display's wiring.

## Pin Functions

The Jetson default uses `rsvd0` function for GPIO pins:

- **Pin 29** (soc_gpio32_pq5):
  - Function: rsvd0 (GPIO)
  - Pull: up (0x2)
  - Tristate: drive (0x0)
  - Input: disabled (0x0) - output only

- **Pin 31** (soc_gpio33_pq6):
  - Function: rsvd0 (GPIO)
  - Pull: up (0x2)
  - Tristate: drive (0x0)
  - Input: disabled (0x0) - output only

This differs from Waveshare/Adafruit which use `rsvd1` and have input enabled.

## Manual Installation

If the automated script fails, you can install manually:

```bash
# 1. Compile overlay
sudo dtc -@ -O dtb -o jetson-st7789-default.dtbo jetson-st7789-default.dts

# 2. Install to /boot/
sudo cp jetson-st7789-default.dtbo /boot/

# 3. Detect base DTB
FDT=$(ls /boot/dtb/kernel_tegra*.dtb | head -n1)

# 4. Backup boot config
sudo cp /boot/extlinux/extlinux.conf /boot/extlinux/extlinux.conf.backup

# 5. Get APPEND line from primary entry
APPEND_LINE=$(grep "APPEND" /boot/extlinux/extlinux.conf | grep -v "^#" | head -n1)

# 6. Add new boot entry
sudo tee -a /boot/extlinux/extlinux.conf << EOF

LABEL JetsonDefault
	MENU LABEL ST7789 Default Config (SPI1 + GPIO 29, 31)
	LINUX /boot/Image
	FDT $FDT
	INITRD /boot/initrd
	$APPEND_LINE
	OVERLAYS /boot/jetson-st7789-default.dtbo
EOF

# 7. Set as default
sudo sed -i 's/^DEFAULT .*/DEFAULT JetsonDefault/' /boot/extlinux/extlinux.conf

# 8. Reboot
sudo reboot
```

## Success Checklist

- [ ] install_default_overlay.sh completed successfully
- [ ] Overlay installed to /boot/jetson-st7789-default.dtbo
- [ ] Boot entry "JetsonDefault" created
- [ ] Set as DEFAULT in extlinux.conf
- [ ] Rebooted system
- [ ] Pin 29 shows configured as GPIO
- [ ] Pin 31 shows configured as GPIO
- [ ] test_jetson_default.py passes
- [ ] Can use display with pins 29/31

## Alternative: No Overlay Needed?

If pins 29 and 31 are already configured as GPIO on your Jetson (check with `pin_inspector.py`), you may not need this overlay at all! The overlay is only needed if the pins aren't already set up as GPIO.

---

**Need help?** Check OVERLAYS_MASTER_GUIDE.md for complete documentation.
