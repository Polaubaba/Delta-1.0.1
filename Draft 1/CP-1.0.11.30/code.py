import board
import busio
import digitalio
import displayio
import adafruit_displayio_ssd1306
import terminalio
from adafruit_display_text import label
import time
import mfrc522  # CircuitPython-compatible MFRC522 library

# LED Setup
led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT

# Release any existing displays
displayio.release_displays()

# Set up I2C communication for OLED Display
i2c = busio.I2C(scl=board.GP5, sda=board.GP4)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Create a display group
group = displayio.Group()

# Setup I2C for RFID-RC522
i2c_rfid = busio.I2C(scl=board.GP7, sda=board.GP6)  # Define correct I2C pins for RFID
rc522 = adafruit_mfrc522.MFRC522(i2c_rfid, addr=0x28)  # Default I2C address for MFRC522

def update_text(new_text):
    """ Update the OLED Display with new text """
    while len(group) > 0:
        group.pop()

    text_label = label.Label(terminalio.FONT, text=new_text, color=0xFFFFFF, x=10, y=30)
    group.append(text_label)
    display.root_group = group  # Assign updated group to the display

print("Ready to scan RFID cards...")

while True:
    # Blink LED
    led.value = True
    time.sleep(0.5)
    led.value = False
    time.sleep(0.5)
    
    # Check if a card is detected
    if rc522.read_card():
        uid = rc522.get_uid()  # Get UID of the RFID card
        if uid:
            card_id = "".join(f"{byte:02X}" for byte in uid)
            print(f"Card Detected: {card_id}")
            
            # Display card UID on OLED
            update_text(f"Card: {card_id}")

    time.sleep(1)
