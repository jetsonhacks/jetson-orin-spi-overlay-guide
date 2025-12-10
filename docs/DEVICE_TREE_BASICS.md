# Device Tree Basics for Jetson

## What is a Device Tree?

A **device tree** is a data structure that describes the hardware configuration of a system. It tells the Linux kernel:
- What hardware devices exist
- How they're connected
- What resources they use (memory addresses, interrupts, pins)
- How to configure them

On Jetson, the device tree is compiled into a binary format (.dtb file) that the bootloader loads before starting the kernel.

## Why Device Trees on Jetson?

Jetson uses device trees because:
1. **Hardware flexibility** - Same kernel can boot different hardware configurations
2. **Runtime configuration** - Change hardware setup without recompiling the kernel
3. **Modularity** - Overlays can add/modify configuration without changing base tree
4. **Standard approach** - Follows Linux ARM conventions

## Device Tree Structure

### Base Device Tree (.dtb)

The base device tree describes the entire system:
- CPU configuration
- Memory layout
- Built-in peripherals (SPI, I2C, GPIO, etc.)
- Default pin configurations

Example path: `/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb`

### Device Tree Overlay (.dtbo)

An overlay modifies the base tree:
- Changes specific pins
- Enables/disables devices
- Adds new device nodes
- Overrides default settings

Example: `jetson-st7789-waveshare.dtbo`

## Device Tree Syntax

### Basic Structure

```dts
/dts-v1/;
/plugin/;

/ {
    overlay-name = "My Overlay";
    compatible = "nvidia,tegra234";
    
    fragment@0 {
        target-path = "/path/to/node";
        __overlay__ {
            // Your modifications here
        };
    };
};
```

### Key Elements

#### 1. Header
```dts
/dts-v1/;        // Version declaration
/plugin/;         // This is an overlay (not a full tree)
```

#### 2. Root Properties
```dts
/ {
    overlay-name = "Description";
    compatible = "nvidia,tegra234";  // Matches Jetson Orin
    ...
};
```

#### 3. Fragments

Fragments target specific parts of the device tree:

```dts
fragment@0 {
    target-path = "/pinmux@2430000/pinmux_default";
    __overlay__ {
        // Pin configuration changes
    };
};
```

### Pin Configuration

#### GPIO Pin Example

```dts
soc_gpio32_pq5 {
    nvidia,pins = "soc_gpio32_pq5";
    nvidia,function = "rsvd0";        // GPIO function
    nvidia,pull = <0x2>;               // Pull-up
    nvidia,tristate = <0x0>;           // Drive (not tristate)
    nvidia,enable-input = <0x0>;       // Output only
};
```

#### SPI Pin Example

```dts
spi1_mosi_pz5 {
    nvidia,pins = "spi1_mosi_pz5";
    nvidia,function = "spi1";          // SPI1 function
    nvidia,pull = <0x1>;               // Pull-down
    nvidia,tristate = <0x0>;           // Drive
    nvidia,enable-input = <0x1>;       // Input enabled
};
```

### Pin Properties Explained

| Property | Values | Meaning |
|----------|--------|---------|
| `nvidia,function` | "spi1", "rsvd0", "rsvd1", etc. | Pin function/mode |
| `nvidia,pull` | 0x0 (none), 0x1 (down), 0x2 (up) | Pull resistor |
| `nvidia,tristate` | 0x0 (drive), 0x1 (tristate) | Output enable |
| `nvidia,enable-input` | 0x0 (disabled), 0x1 (enabled) | Input buffer |

### Complete Example: ST7789 Waveshare

```dts
/dts-v1/;
/plugin/;

/ {
    overlay-name = "Jetson ST7789 Waveshare Configuration";
    compatible = "nvidia,p3768-0000+p3767-0005", "nvidia,tegra234";
    
    // Configure GPIO pins for DC and RST
    fragment@0 {
        target-path = "/pinmux@2430000/pinmux_default";
        __overlay__ {
            // Pin 13 (RST) - Set as GPIO
            spi3_sck_py0 {
                nvidia,pins = "spi3_sck_py0";
                nvidia,function = "rsvd1";
                nvidia,pull = <0x0>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x1>;
            };
            
            // Pin 22 (DC) - Set as GPIO
            spi3_miso_py1 {
                nvidia,pins = "spi3_miso_py1";
                nvidia,function = "rsvd1";
                nvidia,pull = <0x0>;
                nvidia,tristate = <0x0>;
                nvidia,enable-input = <0x1>;
            };
        };
    };
    
    // Configure SPI1 pins
    fragment@1 {
        target-path = "/pinmux@2430000/pinmux_default";
        __overlay__ {
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

## Compilation

### Compile .dts to .dtbo

```bash
dtc -@ -O dtb -o output.dtbo input.dts
```

Options:
- `-@` - Generate symbols (required for overlays)
- `-O dtb` - Output as device tree blob
- `-o output.dtbo` - Output filename
- `input.dts` - Input source file

### Check for Errors

The compiler will report syntax errors:
```
Error: input.dts:45.1-8 syntax error
```

Common issues:
- Missing semicolons
- Incorrect property format
- Invalid node names
- Mismatched braces

## Finding Pin Information

### 1. Check Jetson Pin Header

Physical pin numbers (1-40) on the 40-pin header.

### 2. Find SoC Pin Name

Use NVIDIA's pinmux spreadsheet or documentation:
- Physical Pin 29 → `soc_gpio32_pq5`
- Physical Pin 13 → `spi3_sck_py0`

### 3. Determine Function

GPIO pins can have multiple functions:
- `rsvd0` - Often used for GPIO
- `rsvd1` - Alternative GPIO function
- `spi1`, `i2c3`, etc. - Specific peripheral functions

### 4. Configure Properties

Set pull, tristate, and input enable based on your needs:
- **Output pins** (DC, RST): `enable-input = 0x0`
- **Bidirectional pins** (MISO): `enable-input = 0x1`
- **Strong drive**: `tristate = 0x0`

## Debugging Device Trees

### View Current Configuration

```bash
# See all pinmux settings
sudo cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinmux-pins

# Check specific GPIO chip
sudo cat /sys/kernel/debug/gpio
```

### Check Overlay Loading

```bash
# Boot messages
dmesg | grep -i overlay

# Pinmux changes
dmesg | grep -i pinmux
```

### Verify Pin Configuration

```bash
# Use our pin inspector tool
sudo python3 tools/pin_inspector.py 29

# Manual check
gpioinfo | grep "line 106"
```

## Best Practices

### 1. Start with Working Example
- Copy an existing overlay
- Modify incrementally
- Test after each change

### 2. Document Your Changes
- Add comments explaining pin purposes
- Note physical pin numbers
- Include wiring diagram in README

### 3. Use Descriptive Names
```dts
overlay-name = "ST7789 Display - Waveshare Configuration";
```

### 4. Test Thoroughly
- Verify pins with pin_inspector
- Test hardware functionality
- Check for conflicts

### 5. Keep Overlays Focused
- One overlay per device or configuration
- Don't modify unrelated pins
- Make overlays independent

## Common Patterns

### GPIO Pin Configuration
```dts
my_gpio_pin {
    nvidia,pins = "soc_gpio32_pq5";
    nvidia,function = "rsvd0";       // GPIO
    nvidia,pull = <0x2>;              // Pull-up
    nvidia,tristate = <0x0>;          // Drive
    nvidia,enable-input = <0x0>;      // Output only
};
```

### SPI Pin Configuration
```dts
spi_data_pin {
    nvidia,pins = "spi1_mosi_pz5";
    nvidia,function = "spi1";         // SPI function
    nvidia,pull = <0x1>;              // Pull-down
    nvidia,tristate = <0x0>;          // Drive
    nvidia,enable-input = <0x1>;      // Bidirectional
};
```

### Multiple Pin Fragment
```dts
fragment@0 {
    target-path = "/pinmux@2430000/pinmux_default";
    __overlay__ {
        pin1_config { /* ... */ };
        pin2_config { /* ... */ };
        pin3_config { /* ... */ };
    };
};
```

## Further Reading

- [Linux Device Tree Documentation](https://www.kernel.org/doc/Documentation/devicetree/)
- [Device Tree Specification](https://www.devicetree.org/)
- [NVIDIA Jetson Linux Developer Guide](https://docs.nvidia.com/jetson/archives/r36.4/DeveloperGuide/)

## Next Steps

- [FDT Configuration](FDT_CONFIGURATION.md) - Understanding base device trees
- [Bootloader Setup](BOOTLOADER_SETUP.md) - Loading overlays
- [Pin Configuration](PIN_CONFIGURATION.md) - Detailed pinmux guide

---

Return to [Main README](../README.md)
