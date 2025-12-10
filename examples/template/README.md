# Device Tree Overlay Template

This template provides a starting point for creating device tree overlays for SPI devices on Jetson Orin.

## Files

- `device-overlay-template.dts` - Device tree source template
- `install_overlay_template.sh` - Installation script template
- `README.md` - This file

## Quick Start

### 1. Copy the Template

```bash
cd examples/
cp -r template/ mydevice/
cd mydevice/
```

### 2. Customize the Device Tree Source

Edit `device-overlay-template.dts`:

```bash
nano device-overlay-template.dts
```

**Key changes to make:**

1. **Update overlay name:**
   ```dts
   overlay-name = "My Device Name";
   ```

2. **Configure GPIO pins:**
   - Choose physical pins for control signals (DC, RST, CS, etc.)
   - Find the SoC pin names (see [PIN_CONFIGURATION.md](../../docs/PIN_CONFIGURATION.md))
   - Update the pin configurations in fragment@0

3. **Configure SPI pins (if needed):**
   - Most devices use SPI1 (default in template)
   - Modify fragment@1 if using different SPI bus

4. **Save as your device name:**
   ```bash
   mv device-overlay-template.dts jetson-mydevice.dts
   ```

### 3. Customize the Installer

Edit `install_overlay_template.sh`:

```bash
nano install_overlay_template.sh
```

**Update these variables:**

```bash
DEVICE_NAME="MyDevice"          # Display name
DEVICE_SLUG="mydevice"          # Lowercase filename
DTS_FILE="jetson-${DEVICE_SLUG}.dts"
DTBO_FILE="jetson-${DEVICE_SLUG}.dtbo"

PIN_1=29                        # Your first control pin
PIN_2=31                        # Your second control pin

BOOT_LABEL="${DEVICE_NAME}"
BOOT_MENU_LABEL="${DEVICE_NAME} Configuration"
```

**Save as your device name:**
```bash
mv install_overlay_template.sh install_mydevice_overlay.sh
chmod +x install_mydevice_overlay.sh
```

### 4. Test Your Configuration

```bash
# Compile and install
sudo ./install_mydevice_overlay.sh

# Reboot when prompted
sudo reboot

# Verify pins
sudo python3 ../../tools/pin_inspector.py <your_pin_1>
sudo python3 ../../tools/pin_inspector.py <your_pin_2>
```

## Example: Creating an OLED Display Overlay

Let's say you have an SSD1306 OLED display that uses:
- Pin 29 for DC (Data/Command)
- Pin 31 for RST (Reset)
- Standard SPI1 pins (19, 23, 24)

### Step 1: Copy Template

```bash
cp -r template/ ssd1306/
cd ssd1306/
```

### Step 2: Edit Device Tree

`jetson-ssd1306.dts`:
```dts
/dts-v1/;
/plugin/;

/ {
    overlay-name = "SSD1306 OLED Display";
    compatible = "nvidia,p3768-0000+p3767-0005", "nvidia,tegra234";
    
    fragment@0 {
        target-path = "/pinmux@2430000/pinmux_default";
        __overlay__ {
            // Pin 29 - DC signal
            soc_gpio32_pq5 {
                nvidia,pins = "soc_gpio32_pq5";
                nvidia,function = "rsvd0";
                nvidia,pull = <0x2>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x0>;
            };
            
            // Pin 31 - RST signal
            soc_gpio33_pq6 {
                nvidia,pins = "soc_gpio33_pq6";
                nvidia,function = "rsvd0";
                nvidia,pull = <0x2>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x0>;
            };
        };
    };
    
    fragment@1 {
        target-path = "/pinmux@2430000/pinmux_default";
        __overlay__ {
            // Standard SPI1 configuration
            spi1_mosi_pz5 {
                nvidia,pins = "spi1_mosi_pz5";
                nvidia,function = "spi1";
                nvidia,pull = <0x1>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x1>;
            };
            
            spi1_miso_pz4 {
                nvidia,pins = "spi1_miso_pz4";
                nvidia,function = "spi1";
                nvidia,pull = <0x1>;
                nvidia,tristate = <0x1>;
                nvidia,enable-input = <0x1>;
            };
            
            spi1_sck_pz3 {
                nvidia,pins = "spi1_sck_pz3";
                nvidia,function = "spi1";
                nvidia,pull = <0x1>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x1>;
            };
            
            spi1_cs0_pz6 {
                nvidia,pins = "spi1_cs0_pz6";
                nvidia,function = "spi1";
                nvidia,pull = <0x2>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x1>;
            };
            
            spi1_cs1_pz7 {
                nvidia,pins = "spi1_cs1_pz7";
                nvidia,function = "spi1";
                nvidia,pull = <0x2>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x1>;
            };
        };
    };
};
```

### Step 3: Edit Installer

`install_ssd1306_overlay.sh`:
```bash
#!/bin/bash
# ... (keep the template header) ...

DEVICE_NAME="SSD1306"
DEVICE_SLUG="ssd1306"
DTS_FILE="jetson-${DEVICE_SLUG}.dts"
DTBO_FILE="jetson-${DEVICE_SLUG}.dtbo"

PIN_1=29    # DC
PIN_2=31    # RST

BOOT_LABEL="${DEVICE_NAME}"
BOOT_MENU_LABEL="${DEVICE_NAME} OLED Display"

# ... (rest of template) ...

# Update pin description in summary
echo "Pin Configuration:"
echo "  Pin ${PIN_1} - DC (Data/Command)"
echo "  Pin ${PIN_2} - RST (Reset)"
```

### Step 4: Install and Test

```bash
chmod +x install_ssd1306_overlay.sh
sudo ./install_ssd1306_overlay.sh
# Reboot when prompted
```

## Pin Selection Tips

### Choosing Pins for GPIO

1. **Check availability:**
   ```bash
   sudo python3 ../../tools/pin_inspector.py <pin_number>
   ```

2. **Avoid conflicts:**
   - Don't use pins already configured for other functions
   - Check your hardware schematic

3. **Consider electrical characteristics:**
   - Output pins: Use `enable-input = 0x0`
   - Bidirectional: Use `enable-input = 0x1`
   - Pull-up for active-low signals
   - Pull-down for active-high signals

### Common GPIO Pin Choices

| Physical Pin | SoC Name | Function | Notes |
|--------------|----------|----------|-------|
| 29 | soc_gpio32_pq5 | rsvd0 | Good for GPIO |
| 31 | soc_gpio33_pq6 | rsvd0 | Good for GPIO |
| 13 | spi3_sck_py0 | rsvd1 | Can be GPIO |
| 18 | spi3_cs0_py3 | rsvd1 | Can be GPIO |
| 22 | spi3_miso_py1 | rsvd1 | Can be GPIO |

## SPI Bus Options

### SPI1 (Most Common)

Physical pins: 19 (MOSI), 21 (MISO), 23 (SCLK), 24 (CS0), 26 (CS1)

Device: `/dev/spidev0.0` or `/dev/spidev0.1`

**Use when:** Standard 40-pin header SPI

### Other SPI Buses

Consult Jetson documentation for:
- SPI0
- SPI2
- SPI3

## Testing Your Overlay

### 1. Verify Compilation

```bash
dtc -@ -O dtb -o test.dtbo jetson-mydevice.dts
# Should complete without errors
```

### 2. Check Pin Configuration

After installing and rebooting:
```bash
sudo python3 ../../tools/pin_inspector.py <pin_number>
```

Expected output:
```
✓ Pin is configured as GPIO and ready to use!
```

### 3. Test Hardware

```bash
# Blink test
sudo python3 ../../tools/pin_inspector.py <pin_number> --blink

# Or write your own test
```

## Common Issues

### Compilation Errors

```
Error: syntax error at line XX
```

**Fix:** Check .dts file syntax:
- Missing semicolons
- Incorrect brackets
- Invalid property format

### Pins Not Configured

**Fix:** 
1. Check boot configuration:
   ```bash
   cat /boot/extlinux/extlinux.conf | grep OVERLAYS
   ```
2. Verify overlay is loaded:
   ```bash
   dmesg | grep -i overlay
   ```
3. Reboot if needed

### Wrong Function

**Fix:** Change `nvidia,function`:
- GPIO: "rsvd0" or "rsvd1"
- SPI: "spi0", "spi1", etc.
- I2C: "i2c1", "i2c2", etc.

## Next Steps

1. **Test thoroughly** on real hardware
2. **Document** your configuration
3. **Share** your overlay with the community!

## Resources

- [Device Tree Basics](../../docs/DEVICE_TREE_BASICS.md)
- [FDT Configuration](../../docs/FDT_CONFIGURATION.md)
- [Pin Configuration](../../docs/PIN_CONFIGURATION.md)
- [ST7789 Example](../st7789/) - Complete working example

---

Return to [Main README](../../README.md)
