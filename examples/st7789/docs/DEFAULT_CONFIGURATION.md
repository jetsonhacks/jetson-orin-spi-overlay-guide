# Default Configuration and Recommendations

## Default Pinout: Jetson (pins 29, 31)

The **Jetson preset** using pins 29 and 31 is the **recommended default** for Jetson Orin and Xavier hardware.

### Why Jetson as Default?

1. **Native Jetson pinout** - Designed specifically for Jetson hardware
2. **Established convention** - Used in existing Jetson ST7789 projects
3. **Best for custom displays** - When wiring your own connections
4. **Backward compatible** - Matches existing driver defaults

### Pin Assignments

```
Jetson Default (Recommended):
  DC  = Pin 29 (soc_gpio32_pq5)
  RST = Pin 31 (soc_gpio33_pq6)
  BL  = Pin 17 (3.3V)
```

## When to Use Other Presets

### Waveshare Preset
Use when you have a **Waveshare 2inch LCD Module** that's already wired according to Raspberry Pi pinout:

```
Waveshare (Raspberry Pi compatible):
  DC  = Pin 22 (spi3_miso_py1)
  RST = Pin 13 (spi3_sck_py0)
  BL  = Pin 17 (3.3V)
```

**When to use:**
- You bought a Waveshare display
- Following Waveshare's documentation
- Display is already wired to pins 13 and 22

### Adafruit Preset
Use when you have an **Adafruit 2.0" 320x240 IPS TFT** wired according to their documentation:

```
Adafruit (Raspberry Pi compatible):
  DC  = Pin 22 (spi3_miso_py1)
  RST = Pin 18 (spi3_cs0_py3)
  BL  = Pin 17 (3.3V)
```

**When to use:**
- You bought an Adafruit display
- Following Adafruit's documentation
- Display is already wired to pins 18 and 22

## Preset Order in Code

The presets are ordered by **priority/recommendation**:

```python
PRESETS = {
    'jetson': JETSON_PINS,      # 1st - Default/recommended
    'waveshare': WAVESHARE_PINS, # 2nd - Popular RPi module
    'adafruit': ADAFRUIT_PINS,   # 3rd - Popular RPi module
}
```

When listing presets, Jetson appears first:

```python
>>> from jetson_st7789 import list_presets
>>> for name, desc in list_presets().items():
...     print(f"{name}: {desc}")
jetson: Default pinout for Jetson Orin/Xavier (pins 29, 31)
waveshare: Waveshare 2inch LCD Module (ST7789V) - Raspberry Pi compatible
adafruit: Adafruit 2.0" 320x240 IPS TFT (ST7789) - Raspberry Pi compatible
```

## Installation

Each configuration has its own automated installation script:

```bash
# For Jetson default (recommended)
sudo ./install_default_overlay.sh

# For Waveshare
sudo ./install_waveshare_overlay.sh

# For Adafruit
sudo ./install_adafruit_overlay.sh
```

Each script will:
- Compile the device tree overlay
- Install to /boot/
- Configure the bootloader with proper FDT and OVERLAYS
- Create a new boot entry
- Prompt for reboot

## Usage Examples

### Recommended: Jetson Default

```python
from jetson_st7789 import from_preset

# Use Jetson default pinout (pins 29, 31)
display = from_preset('jetson')
display.fill((255, 0, 0))
```

### With Waveshare Display

```python
from jetson_st7789 import from_preset

# Use Waveshare pinout (pins 13, 22)
display = from_preset('waveshare')
display.fill((0, 255, 0))
```

### With Adafruit Display

```python
from jetson_st7789 import from_preset

# Use Adafruit pinout (pins 18, 22)
display = from_preset('adafruit')
display.fill((0, 0, 255))
```

## Documentation Priority

The documentation is structured to reflect this priority:

1. **JETSON_DEFAULT_OVERLAY_README.md** - Primary documentation
2. **WAVESHARE_OVERLAY_README.md** - For Waveshare displays
3. **ADAFRUIT_OVERLAY_README.md** - For Adafruit displays
4. **OVERLAYS_MASTER_GUIDE.md** - Complete overview

## Quick Decision Guide

**Choose Jetson preset when:**
- ✅ Building a custom project
- ✅ Wiring display yourself
- ✅ Following Jetson documentation
- ✅ No specific manufacturer pinout to follow

**Choose Waveshare preset when:**
- ✅ You have a Waveshare display
- ✅ Display is wired per Waveshare docs
- ✅ Using Raspberry Pi compatible wiring

**Choose Adafruit preset when:**
- ✅ You have an Adafruit display
- ✅ Display is wired per Adafruit docs
- ✅ Using Raspberry Pi compatible wiring

## Summary

| Aspect | Jetson | Waveshare | Adafruit |
|--------|--------|-----------|----------|
| **Priority** | 1st (Default) | 2nd | 3rd |
| **Use Case** | Custom/Native | RPi-compatible | RPi-compatible |
| **DC Pin** | 29 | 22 | 22 |
| **RST Pin** | 31 | 13 | 18 |
| **BL Pin** | 17 | 17 | 17 |
| **When** | Default choice | Have Waveshare HW | Have Adafruit HW |
| **Installer** | install_default_overlay.sh | install_waveshare_overlay.sh | install_adafruit_overlay.sh |

**Bottom line:** If you're not sure which to use, start with **Jetson default** (pins 29, 31).

## Device Tree Overlay Files

Match the overlay to your chosen preset:

```bash
# For Jetson default (recommended)
jetson-st7789-default.dts → jetson-st7789-default.dtbo
install_default_overlay.sh

# For Waveshare
jetson-st7789-waveshare.dts → jetson-st7789-waveshare.dtbo
install_waveshare_overlay.sh

# For Adafruit
jetson-st7789-adafruit.dts → jetson-st7789-adafruit.dtbo
install_adafruit_overlay.sh
```

All three overlays are provided so you can choose based on your hardware.

## Backlight Pin (BL)

All three configurations use **Pin 17 (3.3V)** for the backlight:
- Pin 17 provides constant 3.3V power
- No PWM control (always full brightness)
- Simple and reliable
- No additional GPIO configuration needed

If you need PWM backlight control, you would need to:
1. Choose a PWM-capable pin
2. Modify the device tree overlay
3. Add PWM configuration to your code

For most applications, constant 3.3V on Pin 17 is sufficient.

---

**Recommendation:** Unless you have a specific reason to use Waveshare or Adafruit pinouts (i.e., you have that hardware), use the **Jetson default** configuration with pins 29 and 31.
