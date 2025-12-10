#!/usr/bin/env python3
"""
Jetson Orin Nano Comprehensive Pin Inspector
Analyzes 40-pin expansion header pins from first principles using kernel debugfs

This tool helps diagnose pin configurations, mux settings, and GPIO availability
on NVIDIA Jetson platforms. Essential for troubleshooting display driver issues.

Usage:
    sudo python3 pin_inspector.py <PIN_NUMBER> [--blink]
    
Examples:
    sudo python3 pin_inspector.py 29              # Inspect pin 29 (DC pin)
    sudo python3 pin_inspector.py 31              # Inspect pin 31 (RST pin)
    sudo python3 pin_inspector.py 29 --blink      # Test pin 29 with blink
"""

import os
import re
import sys
import subprocess

# Official pin mappings from NVIDIA headers
HEADER_PIN_NAMES = {
    7:  "soc_gpio59_pac6",
    11: "uart1_rts_pr4",
    12: "soc_gpio41_ph7",
    13: "spi3_sck_py0",
    15: "soc_gpio39_pn1",
    16: "spi3_cs1_py4",
    18: "spi3_cs0_py3",
    19: "spi1_mosi_pz5",
    21: "spi1_miso_pz4",
    22: "spi3_miso_py1",
    23: "spi1_sck_pz3",
    24: "spi1_cs0_pz6",
    26: "spi1_cs1_pz7",
    29: "soc_gpio32_pq5",
    31: "soc_gpio33_pq6",
    32: "soc_gpio19_pg6",
    33: "soc_gpio21_ph0",
    35: "soc_gpio44_pi2",
    36: "uart1_cts_pr5",
    37: "spi3_mosi_py2",
    38: "soc_gpio43_pi1",
    40: "soc_gpio42_pi0",
    # I2C pins
    3:  "gen2_i2c_sda_pdd0",
    5:  "gen2_i2c_scl_pcc7",
    27: "gen1_i2c_sda_pi4",
    28: "gen1_i2c_scl_pi3",
    # UART pins
    8:  "uart1_tx_pr2",
    10: "uart1_rx_pr3",
}

PINCTRL_BASE = "/sys/kernel/debug/pinctrl"
GPIO_BASE = "/sys/class/gpio"

class PinInfo:
    """Container for comprehensive pin information"""
    
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self.soc_name = HEADER_PIN_NAMES.get(pin_num, "unknown")
        self.controller = None
        self.controller_pin_num = None
        self.available_functions = []
        self.current_mux_owner = None
        self.current_gpio_owner = None
        self.is_hogged = False
        self.gpio_chip = None
        self.gpio_line = None
        self.gpio_direction = None
        self.gpio_value = None
        
    def __str__(self):
        lines = [
            f"\n{'='*70}",
            f"PIN {self.pin_num} ANALYSIS",
            f"{'='*70}",
            f"SoC Pin Name:        {self.soc_name}",
            f"Pinmux Controller:   {self.controller or 'NOT FOUND'}",
        ]
        
        if self.controller_pin_num is not None:
            lines.append(f"Controller Pin #:    {self.controller_pin_num}")
            
        lines.append(f"\n--- CURRENT STATE ---")
        lines.append(f"Mux Owner:           {self.current_mux_owner or 'UNCLAIMED'}")
        lines.append(f"GPIO Owner:          {self.current_gpio_owner or 'UNCLAIMED'}")
        lines.append(f"Hogged at boot:      {'YES' if self.is_hogged else 'NO'}")
        
        if self.gpio_chip and self.gpio_line is not None:
            lines.append(f"\n--- GPIO INFO ---")
            lines.append(f"GPIO Chip:           {self.gpio_chip}")
            lines.append(f"GPIO Line:           {self.gpio_line}")
            lines.append(f"Direction:           {self.gpio_direction or 'unknown'}")
            if self.gpio_value is not None:
                lines.append(f"Current Value:       {self.gpio_value}")
        
        if self.available_functions:
            lines.append(f"\n--- AVAILABLE FUNCTIONS ---")
            for func in self.available_functions:
                marker = " (GPIO)" if func in ["gp", "rsvd0", "rsvd1", "rsvd2", "rsvd3"] else ""
                lines.append(f"  - {func}{marker}")
        
        lines.append(f"{'='*70}\n")
        return "\n".join(lines)

def find_pin_in_controller(pin_name, controller_path):
    """Find pin in a specific controller's pins file"""
    pins_file = os.path.join(controller_path, "pins")
    if not os.path.exists(pins_file):
        return None
        
    try:
        with open(pins_file, 'r') as f:
            for line in f:
                # Format: pin 105 (SOC_GPIO32_PQ5) 105:tegra234-gpio  2430000.pinmux
                if pin_name.upper() in line.upper():
                    match = re.search(r'pin (\d+)', line)
                    if match:
                        return int(match.group(1))
    except IOError:
        pass
    return None

def get_available_functions(pin_name, controller_path):
    """Get all functions available for this pin"""
    funcs_file = os.path.join(controller_path, "pinmux-functions")
    if not os.path.exists(funcs_file):
        return []
        
    functions = []
    try:
        with open(funcs_file, 'r') as f:
            for line in f:
                if pin_name in line:
                    # Format: function 7: rsvd0, groups = [ ... pin_name ... ]
                    match = re.search(r'function \d+: (\w+),', line)
                    if match:
                        functions.append(match.group(1))
    except IOError:
        pass
    
    return sorted(set(functions))

def get_current_pinmux_state(pin_name, controller_path):
    """Get current mux and GPIO ownership"""
    pinmux_file = os.path.join(controller_path, "pinmux-pins")
    if not os.path.exists(pinmux_file):
        return None, None, False
        
    try:
        with open(pinmux_file, 'r') as f:
            for line in f:
                if pin_name.upper() in line.upper():
                    # Format: pin 105 (SOC_GPIO32_PQ5): (MUX UNCLAIMED) tegra234-gpio:453
                    mux_match = re.search(r'\): ([^\s]+)', line)
                    gpio_match = re.search(r'([^\s]+):(\d+)', line)
                    
                    mux_owner = mux_match.group(1) if mux_match else None
                    if mux_owner == "(MUX" or mux_owner == "UNCLAIMED)":
                        mux_owner = None
                        
                    gpio_owner = None
                    if gpio_match and "UNCLAIMED" not in line:
                        gpio_owner = gpio_match.group(1)
                    
                    is_hogged = "HOG" in line.upper()
                    
                    return mux_owner, gpio_owner, is_hogged
    except IOError:
        pass
    
    return None, None, False

def find_gpio_chip_and_line(gpio_owner_str):
    """Find GPIO chip and line from owner string like tegra234-gpio:453"""
    if not gpio_owner_str or "UNCLAIMED" in gpio_owner_str:
        return None, None
        
    match = re.search(r':(\d+)', gpio_owner_str)
    if not match:
        return None, None
        
    global_gpio = int(match.group(1))
    
    # Try to find which gpiochip this belongs to
    try:
        result = subprocess.run(['gpioinfo'], capture_output=True, text=True)
        current_chip = None
        for line in result.stdout.split('\n'):
            if 'gpiochip' in line:
                current_chip = line.split()[0]
            elif f'line {global_gpio}:' in line or f'line  {global_gpio}:' in line:
                # Extract line number within chip
                match = re.search(r'line\s+(\d+):', line)
                if match:
                    return current_chip, int(match.group(1))
    except:
        pass
    
    return None, None

def get_gpio_direction_value(gpio_owner_str):
    """Get GPIO direction and value if accessible"""
    if not gpio_owner_str:
        return None, None
        
    match = re.search(r':(\d+)', gpio_owner_str)
    if not match:
        return None, None
        
    gpio_num = match.group(1)
    gpio_path = os.path.join(GPIO_BASE, f"gpio{gpio_num}")
    
    direction = None
    value = None
    
    if os.path.exists(gpio_path):
        try:
            with open(os.path.join(gpio_path, "direction"), 'r') as f:
                direction = f.read().strip()
        except IOError:
            pass
            
        try:
            with open(os.path.join(gpio_path, "value"), 'r') as f:
                value = f.read().strip()
        except IOError:
            pass
    
    return direction, value

def inspect_pin(pin_num):
    """Comprehensive pin inspection"""
    info = PinInfo(pin_num)
    
    if info.soc_name == "unknown":
        print(f"Pin {pin_num} is not a GPIO/configurable pin (power/ground)")
        return None
    
    # Search all pinctrl controllers
    for ctrl_dir in os.listdir(PINCTRL_BASE):
        ctrl_path = os.path.join(PINCTRL_BASE, ctrl_dir)
        if not os.path.isdir(ctrl_path):
            continue
            
        pin_num_in_ctrl = find_pin_in_controller(info.soc_name, ctrl_path)
        if pin_num_in_ctrl is not None:
            info.controller = ctrl_dir
            info.controller_pin_num = pin_num_in_ctrl
            info.available_functions = get_available_functions(info.soc_name, ctrl_path)
            
            mux, gpio, hogged = get_current_pinmux_state(info.soc_name, ctrl_path)
            info.current_mux_owner = mux
            info.current_gpio_owner = gpio
            info.is_hogged = hogged
            
            if gpio:
                info.gpio_chip, info.gpio_line = find_gpio_chip_and_line(gpio)
                info.gpio_direction, info.gpio_value = get_gpio_direction_value(gpio)
            
            break
    
    return info

def generate_dts_fragment(info):
    """Generate device tree overlay fragment"""
    if not info.controller or not info.available_functions:
        return None
    
    # Determine best GPIO function
    gpio_funcs = [f for f in info.available_functions if f in ["gp", "rsvd0", "rsvd1", "rsvd2", "rsvd3"]]
    if not gpio_funcs:
        print("\n⚠ WARNING: No GPIO-suitable functions found for this pin!")
        return None
    
    # Prefer rsvd0, then gp, then others
    if "rsvd0" in gpio_funcs:
        gpio_func = "rsvd0"
    elif "gp" in gpio_funcs:
        gpio_func = "gp"
    else:
        gpio_func = gpio_funcs[0]
    
    # Determine controller target
    is_aon = "c300000" in info.controller or "aon" in info.controller.lower()
    target = "&pinmux_aon" if is_aon else "&pinmux"
    fragment_name = "aon" if is_aon else "main"
    
    dts = f"""
/* Device Tree Fragment for Pin {info.pin_num} */
fragment@0 {{
    target = <{target}>;
    __overlay__ {{
        pinctrl-names = "default";
        pinctrl-0 = <&hdr40_pin{info.pin_num}>;
        
        hdr40_pin{info.pin_num}: header-40pin-pin{info.pin_num} {{
            nvidia,pins = "{info.soc_name}";
            nvidia,function = "{gpio_func}";
            nvidia,pull = <0x0>;           /* 0=none, 1=down, 2=up */
            nvidia,tristate = <0x0>;       /* 0=drive, 1=tristate */
            nvidia,enable-input = <0x1>;   /* 0=output only, 1=input enabled */
        }};
    }};
}};

/* Alternative: Output-only configuration */
/* nvidia,enable-input = <0x0>; */

/* Alternative: With pull-up */
/* nvidia,pull = <0x2>; */

/* Alternative: With pull-down */
/* nvidia,pull = <0x1>; */
"""
    return dts

def is_gpio_configured(info):
    """Check if pin is configured as GPIO (hogged and has GPIO functions)"""
    if not info.is_hogged:
        return False
    
    gpio_funcs = [f for f in info.available_functions if f in ["gp", "rsvd0", "rsvd1", "rsvd2", "rsvd3"]]
    return len(gpio_funcs) > 0

def blink_pin(pin_num, cycles=10, interval=0.5):
    """Blink a GPIO pin"""
    try:
        import Jetson.GPIO as GPIO
    except ImportError:
        print("Error: Jetson.GPIO library not found")
        print("Install with: sudo pip3 install Jetson.GPIO")
        return False
    
    try:
        import time
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin_num, GPIO.OUT)
        
        print(f"\n🔄 Blinking pin {pin_num} ({cycles} cycles, {interval}s interval)...")
        print("Press Ctrl+C to stop\n")
        
        for i in range(cycles):
            print(f"Cycle {i+1}/{cycles}: HIGH", end="", flush=True)
            GPIO.output(pin_num, GPIO.HIGH)
            time.sleep(interval)
            
            print(" -> LOW")
            GPIO.output(pin_num, GPIO.LOW)
            time.sleep(interval)
        
        print(f"\n✓ Blink test complete!")
        GPIO.cleanup()
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        GPIO.cleanup()
        return False
    except Exception as e:
        print(f"\n❌ Error during GPIO operation: {e}")
        try:
            GPIO.cleanup()
        except:
            pass
        return False

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Jetson Orin Pin Inspector - Diagnose 40-pin header GPIO configuration")
        print("\nUsage: sudo python3 pin_inspector.py <PIN_NUMBER> [--blink]")
        print("\nExamples:")
        print("  sudo python3 pin_inspector.py 29              # Inspect pin 29 (DC)")
        print("  sudo python3 pin_inspector.py 31              # Inspect pin 31 (RST)")
        print("  sudo python3 pin_inspector.py 29 --blink      # Test with blink")
        print("\nCommon ST7789 display pins:")
        print("  Pin 29: DC (Data/Command)")
        print("  Pin 31: RST (Reset)")
        print("  Pin 19: MOSI (SPI1)")
        print("  Pin 23: SCK (SPI1)")
        print("  Pin 24: CS0 (SPI1)")
        sys.exit(1)
    
    if os.geteuid() != 0:
        print("⚠ Warning: Running without sudo. Some information may be unavailable.")
        print("   GPIO operations require sudo.\n")
    
    try:
        pin_num = int(sys.argv[1])
    except ValueError:
        print("Error: PIN_NUMBER must be an integer")
        sys.exit(1)
    
    if pin_num < 1 or pin_num > 40:
        print("Error: PIN_NUMBER must be between 1 and 40")
        sys.exit(1)
    
    want_blink = "--blink" in sys.argv or "-b" in sys.argv
    
    print(f"Inspecting pin {pin_num}...")
    info = inspect_pin(pin_num)
    
    if info:
        print(info)
        
        # Check if GPIO configured and offer to blink
        if is_gpio_configured(info):
            print("✓ Pin is configured as GPIO and ready to use!")
            
            if want_blink:
                if os.geteuid() != 0:
                    print("\n❌ GPIO operations require sudo privileges")
                    print("   Run with: sudo python3 pin_inspector.py", pin_num, "--blink")
                else:
                    blink_pin(pin_num)
            else:
                print("\n💡 Tip: Add --blink to test GPIO output")
                print(f"   sudo python3 pin_inspector.py {pin_num} --blink")
        else:
            print("⚠ Pin is NOT configured as GPIO")
            print("  Configure it with the device tree fragment shown below:\n")
        
        dts = generate_dts_fragment(info)
        if dts:
            print("--- DEVICE TREE FRAGMENT ---")
            print(dts)
            print("\nℹ Compile with: dtc -@ -O dtb -o overlay.dtbo overlay.dts")
            print("ℹ Install to: /boot/overlay.dtbo")
            print("ℹ Enable in: /boot/extlinux/extlinux.conf (add to APPEND line)")

if __name__ == "__main__":
    main()
