# Adafruit ST7789 Setup for Jetson Orin

## Quick Start

### 1. Install Adafruit Overlay

```bash
chmod +x install_adafruit_overlay.sh
sudo ./install_adafruit_overlay.sh
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
sudo python3 tools/pin_inspector.py 18
sudo python3 tools/pin_inspector.py 22
```

Both should show: "✓ Pin is configured as GPIO and ready to use!"

### 3. Test Adafruit Display

```bash
sudo python3 test_adafruit_default.py
```

If this passes, your Adafruit display is working!

### 4. Use in Code

```python
from jetson_st7789 import from_preset

with from_preset('adafruit') as display:
    display.fill((0, 255, 0))  # Green
```

## Files

- `jetson-st7789-adafruit.dts` - Device tree overlay source
- `install_adafruit_overlay.sh` - Automated installation script
- `test_adafruit_default.py` - Test script

## What It Configures

The overlay configures:
- **Pin 18** (spi3_cs0_py3) as GPIO for RST
- **Pin 22** (spi3_miso_py1) as GPIO for DC
- **SPI1** pins (19, 21, 23, 24, 26) for SPI communication

## Physical Wiring

```
Adafruit Pin -> Jetson Pin
-------------------------------
Vin          -> Pin 1 (3.3V)
GND          -> Pin 6 (Ground)
MOSI         -> Pin 19 (MOSI)
CLK          -> Pin 23 (SCLK)
CS           -> Pin 24 (CE0)
D/C          -> Pin 22 (GPIO)
RST          -> Pin 18 (GPIO)
BL           -> Pin 17 (3.3V)
```

## Boot Configuration

The installer creates a new boot entry in `/boot/extlinux/extlinux.conf`:

```
LABEL Adafruit
	MENU LABEL Adafruit ST7789 Config (SPI0)
	LINUX /boot/Image
	FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
	INITRD /boot/initrd
	APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 ...
	OVERLAYS /boot/jetson-st7789-adafruit.dtbo
```

To revert to original configuration:
```bash
sudo nano /boot/extlinux/extlinux.conf
# Change: DEFAULT Adafruit
# To:     DEFAULT primary
sudo reboot
```

## Comparison with Waveshare

| Display   | DC Pin | RST Pin | BL Pin |
|-----------|--------|---------|--------|
| Adafruit  | 22     | 18      | 17     |
| Waveshare | 22     | 13      | 17     |

Both use the same DC pin (22) and BL pin (17), but different RST pins.

## Troubleshooting

### Overlay doesn't load
```bash
# Check if file exists
ls -l /boot/jetson-st7789-adafruit.dtbo

# Check boot config
cat /boot/extlinux/extlinux.conf | grep -A 5 "LABEL Adafruit"

# Verify overlay is in boot entry
cat /boot/extlinux/extlinux.conf | grep OVERLAYS
```

### Pins not configured
```bash
# Run installer again
sudo ./install_adafruit_overlay.sh

# Reboot
sudo reboot

# Check pins after reboot
sudo python3 tools/pin_inspector.py 18
sudo python3 tools/pin_inspector.py 22
```

### Display not working
```bash
# Check SPI device exists
ls -l /dev/spidev0.0

# Verify physical connections
sudo python3 tools/pin_inspector.py 18 --blink
sudo python3 tools/pin_inspector.py 22 --blink

# Test with slower SPI speed
python3 -c "
from jetson_st7789 import ST7789
d = ST7789(dc_pin=22, rst_pin=18, spi_speed_hz=62500000)
d.fill((0,255,0))
"
```

### Wrong boot entry active
```bash
# Check which entry is default
grep "^DEFAULT" /boot/extlinux/extlinux.conf

# Should show: DEFAULT Adafruit
# If not, edit and change to Adafruit
sudo nano /boot/extlinux/extlinux.conf
```

## Manual Installation

If the automated script fails, you can install manually:

```bash
# 1. Compile overlay
sudo dtc -@ -O dtb -o jetson-st7789-adafruit.dtbo jetson-st7789-adafruit.dts

# 2. Install to /boot/
sudo cp jetson-st7789-adafruit.dtbo /boot/

# 3. Detect base DTB
FDT=$(ls /boot/dtb/kernel_tegra*.dtb | head -n1)

# 4. Backup boot config
sudo cp /boot/extlinux/extlinux.conf /boot/extlinux/extlinux.conf.backup

# 5. Get APPEND line from primary entry
APPEND_LINE=$(grep "APPEND" /boot/extlinux/extlinux.conf | grep -v "^#" | head -n1)

# 6. Add new boot entry
sudo tee -a /boot/extlinux/extlinux.conf << EOF

LABEL Adafruit
	MENU LABEL Adafruit ST7789 Config (SPI0)
	LINUX /boot/Image
	FDT $FDT
	INITRD /boot/initrd
	$APPEND_LINE
	OVERLAYS /boot/jetson-st7789-adafruit.dtbo
EOF

# 7. Set as default
sudo sed -i 's/^DEFAULT .*/DEFAULT Adafruit/' /boot/extlinux/extlinux.conf

# 8. Reboot
sudo reboot
```

## Success Checklist

- [ ] install_adafruit_overlay.sh completed successfully
- [ ] Overlay installed to /boot/jetson-st7789-adafruit.dtbo
- [ ] Boot entry "Adafruit" created
- [ ] Set as DEFAULT in extlinux.conf
- [ ] Rebooted system
- [ ] Pin 18 shows configured as GPIO
- [ ] Pin 22 shows configured as GPIO
- [ ] test_adafruit_default.py passes
- [ ] Can use `from_preset('adafruit')` in code

---

**Need help?** Check OVERLAYS_MASTER_GUIDE.md for complete documentation.
