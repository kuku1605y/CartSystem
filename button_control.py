#!/usr/bin/env python3
import RPi.GPIO as GPIO
import subprocess
import time
import os

# Configuration
BUTTON_PIN = 2        # Using GPIO2 (Physical Pin 3)
SCRIPT = "/home/rahul/run_cart_system.sh"
DEBOUNCE_TIME = 0.3    # Seconds

def run_script():
    print("Executing script...")
    # Using shell=False for better security
    subprocess.Popen(["/bin/bash", SCRIPT])

def button_pressed(channel):
    # Extra debounce protection for GPIO2
    time.sleep(DEBOUNCE_TIME)
    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        # Additional check to avoid false triggers
        for _ in range(3):
            if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                return
            time.sleep(0.05)
        run_script()

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    # Note: GPIO2 already has hardware pull-up
    GPIO.setup(BUTTON_PIN, GPIO.IN)
    
    # Wait for system to fully boot before enabling button
    time.sleep(5)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, 
                         callback=button_pressed, 
                         bouncetime=300)

if __name__ == "__main__":
    setup_gpio()
    try:
        print("Button controller running on GPIO2. Press CTRL+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()