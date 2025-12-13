# FDT (Flattened Device Tree) Configuration

## What is FDT?

**FDT** (Flattened Device Tree) refers to the base device tree binary (.dtb file) that describes your Jetson hardware. The bootloader loads this file to tell the Linux kernel about your system's hardware configuration.

## Why FDT Matters for Overlays

When using device tree overlays, the bootloader must load the correct base FDT file. The overlay is then applied on top of this base tree.

### Bootloader Configuration

Modern Jetson systems use the `overlays=` parameter in the APPEND line:

```
LABEL primary
    MENU LABEL primary kernel
    LINUX /boot/Image
    FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
    INITRD /boot/initrd
    APPEND ${cbootargs} ... overlays=/boot/my-overlay.dtbo
```

**The FDT line specifies the base device tree, and the overlays= parameter specifies which overlay to apply.**

## Finding Your FDT File

### Method 1: Check /boot/dtb/

```bash
ls -lh /boot/dtb/*.dtb
```

For most Jetson Orin Nano systems, you'll see:
```
/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```

### Method 2: Use Our Detection Script

```bash
./tools/detect_fdt.sh
```

Output:
```
/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```

### Method 3: Check Device Tree Compatible String

```bash
cat /proc/device-tree/compatible | tr '\0' '\n'
```

Output:
```
nvidia,p3768-0000+p3767-0005-super
nvidia,p3767-0005
nvidia,tegra234
```

This tells you the hardware identifiers, which correspond to the DTB filename.

### Method 4: Programmatic Detection (for Scripts)

```bash
# Find the first (and usually only) DTB file
FDT_FILE=$(ls /boot/dtb/kernel_tegra*.dtb 2>/dev/null | head -n1)

if [ -z "$FDT_FILE" ]; then
    echo "Error: Could not find base DTB file"
    exit 1
fi

echo "Using FDT: $FDT_FILE"
```

This is what our automated installer scripts use.

## FDT Naming Convention

Jetson FDT files follow this pattern:
```
kernel_tegra<soc>-<carrier>-<module>-<variant>.dtb
```

Examples:

**Jetson Orin Nano:**
```
kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```
- `tegra234` - Tegra X4 SoC (Orin)
- `p3768` - Carrier board (Orin Nano Developer Kit)
- `p3767-0005` - Module variant
- `nv-super` - Configuration variant

**Jetson Orin NX:**
```
kernel_tegra234-p3509-0000+p3767-0000-nv.dtb
```

**Jetson AGX Orin:**
```
kernel_tegra234-p3701-0000-p3737-0000.dtb
```

## When to Specify FDT

### Always Specify When:
- Using device tree overlays
- Creating custom boot entries
- You want explicit control over base device tree

### May Omit When:
- Using the default "primary" boot entry
- Bootloader has correct default configured

**Best Practice:** Always specify FDT explicitly when using overlays for clarity and reliability.

## Multiple FDT Files

Some systems may have multiple DTB files:

```bash
ls /boot/dtb/kernel_tegra*.dtb
```

```
/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv.dtb
/boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
```

The differences might be:
- Different memory configurations
- Different peripheral enablement
- Different power profiles

**Use the one that matches your hardware.** The detection script will choose the first one, which is usually correct.

## Bootloader Configuration Details

### Structure of extlinux.conf

```bash
cat /boot/extlinux/extlinux.conf
```

```
TIMEOUT 30
DEFAULT primary
MENU TITLE L4T boot options

LABEL primary
    MENU LABEL primary kernel
    LINUX /boot/Image
    INITRD /boot/initrd
    APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait ...
    # Note: May or may not have explicit FDT line
```

### Adding Overlays

The installer scripts add the `overlays=` parameter to the APPEND line:

```
LABEL primary
    MENU LABEL primary kernel
    LINUX /boot/Image
    FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
    INITRD /boot/initrd
    APPEND ${cbootargs} ... overlays=/boot/jetson-orin-st7789-waveshare.dtbo
```

### Key Elements

1. **LABEL** - Unique identifier for the boot entry
2. **MENU LABEL** - Human-readable description shown in boot menu
3. **LINUX** - Kernel image path
4. **FDT** - Base device tree path
5. **INITRD** - Initial ramdisk path
6. **APPEND** - Kernel command line parameters (includes overlays=)

### APPEND Line

The APPEND line should be preserved from your existing entry:

```bash
# Extract APPEND line from primary entry
grep "APPEND" /boot/extlinux/extlinux.conf | grep -v "^#" | head -n1
```

Example output:
```
APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait rootfstype=ext4 mminit_loglevel=4 console=ttyTCU0,115200 firmware_class.path=/etc/firmware fbcon=map:0 video=efifb:off console=tty0
```

This ensures your overlay configuration uses the same kernel parameters as the working default.

## Creating Boot Entries with FDT

### Automated Method (Recommended)

Our installer scripts do this automatically:

```bash
cd examples/st7789/waveshare
sudo ./install.sh
```

The script:
1. Detects FDT automatically
2. Backs up configuration with timestamp
3. Adds overlays= parameter to APPEND line
4. Prompts for reboot

### Manual Method

```bash
# 1. Backup configuration
sudo cp /boot/extlinux/extlinux.conf /boot/extlinux/extlinux.conf.backup

# 2. Edit configuration
sudo nano /boot/extlinux/extlinux.conf

# 3. Add overlays= to APPEND line
# Before: APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait ...
# After:  APPEND ${cbootargs} root=/dev/mmcblk0p1 rw rootwait ... overlays=/boot/my-overlay.dtbo

# 4. Save and reboot
sudo reboot
```

## Verifying FDT Configuration

### Check Boot Entry

```bash
cat /boot/extlinux/extlinux.conf | grep -A 6 "LABEL primary"
```

Should show:
```
LABEL primary
    MENU LABEL primary kernel
    LINUX /boot/Image
    FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb
    INITRD /boot/initrd
    APPEND ${cbootargs} ... overlays=/boot/jetson-orin-st7789-waveshare.dtbo
```

### Verify After Boot

```bash
# Check which device tree was loaded
ls -l /sys/firmware/devicetree/base/

# Check for overlay
dmesg | grep -i overlay

# Check for pinmux changes
dmesg | grep -i pinmux
```

## Troubleshooting FDT Issues

### Problem: Overlay doesn't apply

**Symptoms:**
- Pins not configured
- Hardware doesn't work
- No overlay messages in dmesg

**Solution:**
```bash
# 1. Verify overlays= is in APPEND line
cat /boot/extlinux/extlinux.conf | grep overlays

# 2. Verify overlay file exists
ls -l /boot/jetson-orin-st7789-*.dtbo

# 3. Check for typos in path
cat /boot/extlinux/extlinux.conf | grep APPEND
```

### Problem: Wrong FDT file

**Symptoms:**
- System boots but hardware behaves incorrectly
- Some peripherals don't work

**Solution:**
```bash
# List available DTB files
ls -l /boot/dtb/*.dtb

# Check compatible string
cat /proc/device-tree/compatible | tr '\0' '\n'

# Match the DTB filename to your hardware variant
```

### Problem: FDT path incorrect

**Symptoms:**
- Boot fails or hangs
- Error messages about missing FDT

**Solution:**
```bash
# Verify the path is correct (absolute path from /)
# Wrong:  FDT kernel_tegra234-...
# Wrong:  FDT dtb/kernel_tegra234-...
# Right:  FDT /boot/dtb/kernel_tegra234-...
```

### Problem: Multiple DTB files, unsure which to use

**Solution:**
```bash
# Use the detection script
./tools/detect_fdt.sh

# Or check what the primary entry uses (if any)
grep -A 5 "LABEL primary" /boot/extlinux/extlinux.conf | grep FDT

# When in doubt, use the first one found
ls /boot/dtb/kernel_tegra*.dtb | head -n1
```

## Advanced: FDT Decompilation

You can examine the contents of a DTB file:

```bash
# Install device tree compiler if needed
sudo apt-get install device-tree-compiler

# Decompile DTB to readable format
dtc -I dtb -O dts /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv-super.dtb -o base-tree.dts

# View the source
less base-tree.dts
```

This shows you the complete hardware description, including:
- Pin configurations
- Enabled devices
- Memory layout
- Default settings

**Use case:** Understanding how pins are configured by default before applying overlays.

## Best Practices

1. **Always specify FDT** when using overlays - Don't rely on bootloader defaults
2. **Use absolute paths** - `/boot/dtb/...` not relative paths
3. **Verify file exists** - Check before rebooting
4. **Backup first** - Always backup extlinux.conf before editing
5. **Test incrementally** - Apply one overlay, test, then add more
6. **Document your choice** - Comment why you chose specific FDT
7. **Use automation** - Let installer scripts detect and configure FDT

## Summary

| Aspect | Details |
|--------|---------|
| **What is FDT** | Base device tree binary describing your hardware |
| **File location** | `/boot/dtb/kernel_tegra*.dtb` |
| **When needed** | Always when using device tree overlays |
| **Detection** | Use `detect_fdt.sh` or find first .dtb file |
| **Configuration** | Add `FDT` line to boot entry, overlays= to APPEND |
| **With overlays** | FDT = base, overlays= modifications |

## Next Steps

- [Device Tree Basics](DEVICE_TREE_BASICS.md) - Understanding device trees
- [ST7789 Examples](../examples/st7789/) - Working overlay examples

---

Return to [Main README](../README.md)
