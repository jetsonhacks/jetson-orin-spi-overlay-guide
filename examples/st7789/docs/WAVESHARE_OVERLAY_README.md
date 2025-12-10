# Waveshare ST7789 Setup for Jetson Orin

## Quick Start

### 1. Install Waveshare Overlay

```bash
chmod +x install_waveshare_overlay.sh
sudo ./install_waveshare_overlay.sh
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
sudo python3 tools/pin_inspector.py 13
sudo python3 tools/pin_inspector.py 22
```

Both should show: "✓ Pin is configured as GPIO and ready to use!"

### 3. Test Waveshare Display

```bash
sudo python3 test_waveshare_default.py
```

If this passes, your Waveshare display is working!

### 4. Use in Code

```python
from jetson_st7789 import from_preset

with from_preset('waveshare') as display:
    display.fill((255, 0, 0))  # Red
```

## Files

- `jetson-st7789-waveshare.dts` - Device tree overlay source
- `install_waveshare_overlay.sh` - Automated installation script
- `test_waveshare_default.py` - Test script

## What It Configures

The overlay configures:
- **Pin 13** (spi3_sck_py0) as GPIO for RST
- **Pin 22** (spi3_miso_py1) as GPIO for DC
- **SPI1** pins (19, 21, 23, 24, 26) for SPI communication

## Physical Wiring

```
Waveshare Pin -> Jetson Pin
------------------------------
VCC           -> Pin 1 (3.3V)
GND           -> Pin 6 (Ground)
DIN           -> Pin 19 (MOSI)
CLK           -> Pin 23 (SCLK)
CS            -> Pin 24 (CE0)
DC            -> Pin 22 (GPIO)
RST           -> Pin 13 (GPIO)
BL            -> Pin 17 (3.3V)
```

## Boot Configuration

The installer creates a new boot entry in `/boot/extlinux/extlinux.conf`:

```
LABEL Waveshare
	MENU LABEL Waveshare ST7789 Config
	LINUX /boot/Image
	FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
	INITRD /boot/initrd
	APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 ...
	OVERLAYS /boot/jetson-st7789-waveshare.dtbo
```

To revert to original configuration:
```bash
sudo nano /boot/extlinux/extlinux.conf
# Change: DEFAULT Waveshare
# To:     DEFAULT primary
sudo reboot
```

## Troubleshooting

### Overlay doesn't load
```bash
# Check if file exists
ls -l /boot/jetson-st7789-waveshare.dtbo

# Check boot config
cat /boot/extlinux/extlinux.conf | grep -A 5 "LABEL Waveshare"

# Verify overlay is in boot entry
cat /boot/extlinux/extlinux.conf | grep OVERLAYS
```

### Pins not configured
```bash
# Run installer again
sudo ./install_waveshare_overlay.sh

# Reboot
sudo reboot

# Check pins after reboot
sudo python3 tools/pin_inspector.py 13
sudo python3 tools/pin_inspector.py 22
```

### Display not working
```bash
# Check SPI device exists
ls -l /dev/spidev0.0

# Verify physical connections
sudo python3 tools/pin_inspector.py 13 --blink
sudo python3 tools/pin_inspector.py 22 --blink

# Test with slower SPI speed
python3 -c "
from jetson_st7789 import ST7789
d = ST7789(dc_pin=22, rst_pin=13, spi_speed_hz=62500000)
d.fill((255,0,0))
"
```

### Wrong boot entry active
```bash
# Check which entry is default
grep "^DEFAULT" /boot/extlinux/extlinux.conf

# Should show: DEFAULT Waveshare
# If not, edit and change to Waveshare
sudo nano /boot/extlinux/extlinux.conf
```

## Manual Installation

If the automated script fails, you can install manually:

```bash
# 1. Compile overlay
sudo dtc -@ -O dtb -o jetson-st7789-waveshare.dtbo jetson-st7789-waveshare.dts

# 2. Install to /boot/
sudo cp jetson-st7789-waveshare.dtbo /boot/

# 3. Detect base DTB
FDT=$(ls /boot/dtb/kernel_tegra*.dtb | head -n1)

# 4. Backup boot config
sudo cp /boot/extlinux/extlinux.conf /boot/extlinux/extlinux.conf.backup

# 5. Get APPEND line from primary entry
APPEND_LINE=$(grep "APPEND" /boot/extlinux/extlinux.conf | grep -v "^#" | head -n1)

# 6. Add new boot entry
sudo tee -a /boot/extlinux/extlinux.conf << EOF

LABEL Waveshare
	MENU LABEL Waveshare ST7789 Config
	LINUX /boot/Image
	FDT $FDT
	INITRD /boot/initrd
	$APPEND_LINE
	OVERLAYS /boot/jetson-st7789-waveshare.dtbo
EOF

# 7. Set as default
sudo sed -i 's/^DEFAULT .*/DEFAULT Waveshare/' /boot/extlinux/extlinux.conf

# 8. Reboot
sudo reboot
```

## Success Checklist

- [ ] install_waveshare_overlay.sh completed successfully
- [ ] Overlay installed to /boot/jetson-st7789-waveshare.dtbo
- [ ] Boot entry "Waveshare" created
- [ ] Set as DEFAULT in extlinux.conf
- [ ] Rebooted system
- [ ] Pin 13 shows configured as GPIO
- [ ] Pin 22 shows configured as GPIO
- [ ] test_waveshare_default.py passes
- [ ] Can use `from_preset('waveshare')` in code

---

**Need help?** Check OVERLAYS_MASTER_GUIDE.md for complete documentation.
