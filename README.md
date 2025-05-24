# Smart Product Detection System

![System Overview](hardware/hardware.jpg)

An automated computer vision system that detects products using YOLO object detection and manages a digital cart via Firebase. Designed for Raspberry Pi 4 with LED status indicators.

## Features

- 🛒 Automatic product detection and cart management
- 📷 Real-time camera processing
- 🔴🟢🔵 LED status indicators (Red=No detection, Green=New Item added to cart, Blue=Quantity Updated)
- ☁️ Firebase cloud synchronization
- 🤖 Auto-start on boot

## Hardware Requirements
| Component              | Specification                    |
|------------------------|----------------------------------|
| Raspberry Pi           | 4 (4GB+ recommended)             |
| Camera                 | Official Pi Camera or USB webcam |
| LEDs                   | Red, Green, Blue                 |
| Resistors              | 220Ω (x3)                        |

## Option 1 - One step Initialization 

- Create a firebase project  
- Download Firebase Admin SDK 
- Rename it as serviceAccountKey.json 
- Move file to Cart_system_raspberryPi/
Then run this :

On Windows:
```bash
mkdir CartSystem
cd CartSystem
python -m venv cart_env
Set-ExecutionPolicy Unrestricted -Scope Process
.\cart_env\Scripts\activate
pip install numpy firebase-admin ultralytics pillow tk RPi.GPIO
git clone https://github.com/raahulmorya/Cart_system_raspberryPi
cd Cart_system_raspberryPi
```

On Linux:
```bash
mkdir CartSystem
cd CartSystem
python -m venv cart_env
source cart_env/bin/activate
pip install numpy firebase-admin ultralytics pillow tk RPi.GPIO
git clone https://github.com/raahulmorya/Cart_system_raspberryPi
cd Cart_system_raspberryPi
```
Then switch to [Running the System on Window/Linux](#running-the-system-on-windowlinux)
 
## Option 2 - Create a Virtual Environment
Use the following command to create a virtual environment named myenv:

```bash
python -m venv cart_env
```
This will create a directory cart_env/ containing a standalone Python environment.

## Activate the Virtual Environment

On Windows
```bash
Set-ExecutionPolicy Unrestricted -Scope Process
.\cart_env\Scripts\activate
```

On Linux
Activate it using this command:
```bash
source cart_env/bin/activate
```

Once activated, your terminal will show (cart_env) at the beginning of the prompt.

## Installation

On Windows
```bash
pip install numpy firebase-admin ultralytics pillow tk
```

On Linux
```bash
pip install numpy firebase-admin ultralytics pillow tk 
```
On Linux(Raspberry Pi)
```bash
# 1. Install dependencies
sudo apt update && sudo apt install -y python-pip python-opencv

# 2. Install Python packages
pip install numpy firebase-admin ultralytics pillow tk RPi.GPIO

# 3. Enable camera
sudo raspi-config
# → Interface Options → Camera → Enable
```

## GPIO Wiring
- Green LED  → GPIO 17
- Blue LED   → GPIO 27  
- Red LED    → GPIO 22
- All GND    → Ground (via 220Ω resistors)

## Firebase Setup

- Create Firestore database and name it anything
- Place your serviceAccountKey.json in the project root

Create Collections
```bash
python create_db_structure.py
```

## Running the System on Window/Linux

To test model detection on Windows/Linux
```bash
python test_products.py
```

To detect and add to cart system on Windows/Linux
```bash
python detect_products.py
```

## Running the System on Raspberry Pi 4
Manual Start
```bash
python raspberry_pi_detect_products.py
```

For Automatic Startup (Systemd Service)
If you want this to run automatically on boot:

Create a service file:

```bash
sudo nano /etc/systemd/system/cart_system.service
Paste this configuration:

ini
[Unit]
Description=Cart System Product Detection
After=network.target

[Service]
User=rahul
WorkingDirectory=/home/rahul
ExecStart=/bin/bash -c 'source cart_env/bin/activate && cd Cart_system_raspberryPi && python raspberry_pi_detect_products.py'
Restart=on-failure

[Install]
WantedBy=multi-user.target
Enable and start the service:
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cart_system.service
sudo systemctl start cart_system.service
```
## Live Cart and Checkout
To view Real-Time cart items

In new Terminal
```bash
python smart_cart.py
```
Proceed for checkout 
+ Invoice Generation


## Automate scripts using ssh login
To Enable SSH on Raspberry Pi
-Boot your Raspberry Pi and log in
-Open terminal and run:
```bash
sudo raspi-config
```
Navigate to: Interfacing Options → SSH → Yes → OK → Finish

Reboot if prompted

Setup ssh in Windows
- [Windows Terminal SSH Tutorial](https://learn.microsoft.com/en-us/windows/terminal/tutorials/ssh)

or
Using Git Bash
If you have Git installed, you can use Git Bash which includes SSH:

Open Git Bash from Start menu

Then use ssh normally
or
Using WSL (Windows Subsystem for Linux)
Install WSL: wsl --install in PowerShell (admin)

Then use ssh from the Linux terminal

Once ssh installation done
run this in terminal/git bash
```bash
ssh [USER_NAME]@[RASPBERRY_PI_IP]
```
then Enter password

Now, Create a new script file:

```bash
nano ~/run_cart_system.sh
```
Paste this inside

```bash
#!/bin/bash
cd ~/CartSystem
source cart_env/bin/activate
cd Cart_system_raspberryPi
python raspberry_pi_detect_products_nogui.py
```
Save (Ctrl+O, Enter) and exit (Ctrl+X)

Make the script executable:

```bash
chmod +x ~/run_cart_system.sh
```
Run it:

```bash
~/run_cart_system.sh
```

Next time when login via ssh, simply run

```bash
~/run_cart_system.sh
```


or if not using SSH

## Setting Up a Tactile Button to Run/Stop a Script on Raspberry Pi Startup
Hardware Setup
Choose an available GPIO pin (e.g., GPIO2 )

Connect one side of button to GPIO23

Connect other side to Ground (Pin 14, 20, 30, or 34)

Enable internal pull-up resistor in code

Python Control Script
Create /home/rahul/button_control.py:

```python
#!/usr/bin/env python3
import RPi.GPIO as GPIO
import subprocess
import time
import os
import signal

# Configuration
BUTTON_PIN = 2        # GPIO2 (Physical Pin 3)
SCRIPT = "/home/rahul/run_cart_system.sh"
DEBOUNCE_TIME = 0.3    # Seconds
POLL_INTERVAL = 0.05   # Seconds between button checks
MIN_PRESS_INTERVAL = 2.0  # Minimum seconds between button presses (2 seconds)
RED_LED = 22          # GPIO pin for LED

# Global variable to track script state
script_process = None
last_press_time = 0
last_valid_press_time = 0
button_state = GPIO.HIGH
last_button_state = GPIO.HIGH

def is_script_running():
    """Check if our script is currently running"""
    try:
        # Look for our specific script in process list
        result = subprocess.check_output(["pgrep", "-f", "raspberry_pi_detect_products_nogui.py"])
        pids = result.decode().strip().split('\n')
        return bool(pids[0])  # Check if first PID exists (ignore empty strings)
    except subprocess.CalledProcessError:
        return False

def toggle_script():
    global script_process
    if is_script_running():
        print("Stopping script...")
        GPIO.output(RED_LED, GPIO.LOW)

        # Kill all instances of our script
        result = subprocess.check_output(["pgrep", "-f", "raspberry_pi_detect_products_nogui.py"])
        pids = result.decode().strip().split('\n')

        # Kill all matching PIDs
        for pid in pids:
            if pid:  # Only try to kill non-empty PIDs
                try:
                    subprocess.run(["kill", "-9", pid])
                except:
                    pass
        script_process = None
    else:
        print("Starting script...")
        # Visual feedback with LED
        GPIO.output(RED_LED, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(RED_LED, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RED_LED, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(RED_LED, GPIO.LOW)
        
        script_process = subprocess.Popen(["/bin/bash", SCRIPT])

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Enable pull-up
    GPIO.setup(RED_LED, GPIO.OUT)
    GPIO.output(RED_LED, GPIO.LOW)

def check_button():
    global last_button_state, last_press_time, last_valid_press_time
    
    # Read current button state
    current_state = GPIO.input(BUTTON_PIN)
    
    # Check for state change
    if current_state != last_button_state:
        last_button_state = current_state
        return False
    
    # If button is pressed (LOW) and was previously not pressed
    if current_state == GPIO.LOW:
        current_time = time.time()
        # Check both debounce time and minimum press interval
        if (current_time - last_press_time > DEBOUNCE_TIME and 
            current_time - last_valid_press_time > MIN_PRESS_INTERVAL):
            last_press_time = current_time
            last_valid_press_time = current_time
            return True
    
    return False

if __name__ == "__main__":
    setup_gpio()
    try:
        print(f"Button controller ready on GPIO{BUTTON_PIN}")
        print(f"Press button to START/STOP the script (min {MIN_PRESS_INTERVAL}s between presses)")
        
        # Wait for system stability
        time.sleep(5)
        
        while True:
            if check_button():
                toggle_script()
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        GPIO.cleanup()

```

Make Files Executable
```bash
chmod +x ~/run_cart_system.sh
chmod +x ~/button_control.py
```
Autostart Setup
Create systemd service:

```bash
sudo nano /etc/systemd/system/button_control.service
```
Add this content:

```ini
[Unit]
Description=GPIO2 Button Controller
After=multi-user.target
StartLimitIntervalSec=60

[Service]
ExecStart=/usr/bin/python3 /home/rahul/button_control.py
WorkingDirectory=/home/rahul
Restart=always
RestartSec=5
User=rahul

[Install]
WantedBy=multi-user.target
```
Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable button_control.service
sudo systemctl start button_control.service  
```
