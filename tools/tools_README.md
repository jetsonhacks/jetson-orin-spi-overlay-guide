# Tools Directory

Diagnostic and utility tools for jetson-st7789 development.

## Available Tools

### pin_inspector.py

Comprehensive GPIO pin diagnostic tool for NVIDIA Jetson platforms.

**Quick Start:**
```bash
# Check if pin 29 is configured for GPIO
sudo python3 tools/pin_inspector.py 29

# Check pin 31
sudo python3 tools/pin_inspector.py 31

# Test pin with blink
sudo python3 tools/pin_inspector.py 29 --blink
```

**Use Cases:**
- Verify GPIO configuration before running display driver
- Troubleshoot "GPIO not working" issues
- Generate device tree overlay fragments
- Test GPIO pins with visual blink test
- Debug hardware connections

**Documentation:**  
See [docs/PIN_INSPECTOR_GUIDE.md](../docs/PIN_INSPECTOR_GUIDE.md) for complete usage guide.

**Requirements:**
- Root/sudo access
- Kernel debugfs mounted
- Optional: Jetson.GPIO for blink tests

## Common Workflows

### Before Running Display Driver

Always verify your GPIO pins are configured:

```bash
# 1. Check DC pin (default: 29)
sudo python3 tools/pin_inspector.py 29

# 2. Check RST pin (default: 31) 
sudo python3 tools/pin_inspector.py 31

# Both should show: ✓ Pin is configured as GPIO and ready to use!
```

### If Pins Not Configured

The tool will generate device tree fragments:

```bash
# Generate overlay
sudo python3 tools/pin_inspector.py 29 > pin29_overlay.dts

# Compile
dtc -@ -O dtb -o pin29.dtbo pin29_overlay.dts

# Install
sudo cp pin29.dtbo /boot/
```

### Quick Pin Check Script

```bash
#!/bin/bash
# check_display_pins.sh
echo "Checking ST7789 display pins..."
for pin in 29 31; do
    echo "=== Pin $pin ==="
    sudo python3 tools/pin_inspector.py $pin | grep -E "Pin is"
done
```

## Contributing

To add a new tool:

1. Create your tool in `tools/`
2. Make it executable: `chmod +x tools/your_tool.py`
3. Add documentation to `docs/`
4. Update this README
5. Add usage examples to QUICKSTART.md

## See Also

- [PIN_INSPECTOR_GUIDE.md](../docs/PIN_INSPECTOR_GUIDE.md) - Complete pin inspector documentation
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [SETUP_CHECKLIST.md](../SETUP_CHECKLIST.md) - Development guide
