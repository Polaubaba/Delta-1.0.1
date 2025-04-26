import board
import busio
import digitalio
import displayio
import adafruit_displayio_ssd1306
import terminalio
from adafruit_display_text import label
import time
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.consumer_control import ConsumerControl
from rotaryio import IncrementalEncoder
import usb_hid
import neopixel
import pwmio

# LED Setup
led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT

# Buzzer Setup
buzzer = pwmio.PWMOut(board.GP11, duty_cycle=0, frequency=2000)

def beep():
    buzzer.duty_cycle = 50000  # 50% duty cycle for loud beep
    time.sleep(0.05)
    buzzer.duty_cycle = 0

# Release any existing displays
displayio.release_displays()

# Set up I2C communication for OLED Display
i2c = busio.I2C(scl=board.GP5, sda=board.GP4)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Show startup image
image_file = open("image.bmp", "rb")  # Ensure the file is in the correct location
bitmap = displayio.OnDiskBitmap(image_file)
tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
group = displayio.Group()
group.append(tile_grid)
display.root_group = group
time.sleep(2)  # Show for 2 seconds

group.pop()

# Create a display group
group = displayio.Group()
display.root_group = group
last_display_text = ""

def update_text(new_text):
    """ Update the OLED Display only if the text has changed """
    global last_display_text
    if new_text == last_display_text:
        return  # Prevent unnecessary updates
    last_display_text = new_text
    while len(group) > 0:
        group.pop()
    text_lines = new_text.split("\n")
    for i, line in enumerate(text_lines):
        text_label = label.Label(terminalio.FONT, text=line, color=0xFFFFFF, x=10, y=10 + (i * 12))
        group.append(text_label)
    display.root_group = group

# NeoPixel Setup
NEOPIXEL_PIN = board.GP23
num_pixels = 1
pixels = neopixel.NeoPixel(NEOPIXEL_PIN, num_pixels, brightness=0.5, auto_write=False)

color_map = {
    "Green": (0, 255, 0),
    "Blue": (0, 0, 255),
    "Red": (255, 0, 0),
    "Yellow": (255, 255, 0),
    "Pink": (255, 20, 147),
    "Violet": (138, 43, 226),
    "Orange": (255, 165, 0),
    "Turn OFF": (0, 0, 0)
}

# Rotary Encoder Setup
encoder = IncrementalEncoder(board.GP20, board.GP21)
switch = digitalio.DigitalInOut(board.GP26)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

back_switch = digitalio.DigitalInOut(board.GP22)
back_switch.direction = digitalio.Direction.INPUT
back_switch.pull = digitalio.Pull.UP

cc = ConsumerControl(usb_hid.devices)

# Menu Setup
menu = ["RGB Neo Pixel", "LED BLINK", "KEYBOARD FUNCTIONALITY", "SHOW IMAGE"]
submenu = {
    "RGB Neo Pixel": ["Green", "Blue", "Red", "Yellow", "Pink", "Violet", "Orange", "Turn OFF", "Back"],
    "LED BLINK": ["Turn ON", "Turn OFF", "Back"],
    "KEYBOARD FUNCTIONALITY": ["Turn ON", "Turn OFF", "Back"],
    "SHOW IMAGE": ["Display Image", "Back"]
}
current_menu = menu
menu_stack = []
selected_index = 0
keyboard_mode = False
last_position = encoder.position

def show_image():
    image_file = open("buec.bmp", "rb")  # Ensure the file is in the correct location
    bitmap = displayio.OnDiskBitmap(image_file)
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
    while len(group) > 0:
        group.pop()
    group.append(tile_grid)
    display.root_group = group
    time.sleep(5)
    show_menu()

def show_menu():
    """ Display the menu with highlighting """
    display_text = "\n".join(["> " + item if i == selected_index else "  " + item for i, item in enumerate(current_menu)])
    update_text(display_text)

show_menu()
print("Ready for menu navigation...")

while True:
    if not keyboard_mode:
        current_position = encoder.position
        position_change = current_position - last_position
        if position_change > 0:
            selected_index = (selected_index + 1) % len(current_menu)
            beep()
        elif position_change < 0:
            selected_index = (selected_index - 1) % len(current_menu)
            beep()
        last_position = current_position
        show_menu()

        if not switch.value:  # Select button
            selected_option = current_menu[selected_index]
            if selected_option == "Back":
                if menu_stack:
                    current_menu = menu_stack.pop()
                    selected_index = 0
            elif selected_option in submenu:
                menu_stack.append(current_menu)
                current_menu = submenu[selected_option]
                selected_index = 0
            elif selected_option == "Display Image":
                show_image()
            elif selected_option == "Turn ON" and "KEYBOARD FUNCTIONALITY" in menu_stack:
                keyboard_mode = True
                beep()
            elif selected_option == "Turn OFF" and "KEYBOARD FUNCTIONALITY" in menu_stack:
                keyboard_mode = False
                beep()
            elif selected_option == "Turn ON" and "LED BLINK" in menu_stack:
                led.value = True
                beep()
            elif selected_option == "Turn OFF" and "LED BLINK" in menu_stack:
                led.value = False
                beep()
            elif selected_option in color_map:
                pixels.fill(color_map[selected_option])
                pixels.show()
                beep()
            show_menu()

        if not back_switch.value:  # Back button
            if menu_stack:
                current_menu = menu_stack.pop()
                selected_index = 0
                beep()
                show_menu()
    else:
        current_position = encoder.position
        position_change = current_position - last_position
        if position_change > 0:
            for _ in range(position_change):
                cc.send(ConsumerControlCode.VOLUME_INCREMENT)
        elif position_change < 0:
            for _ in range(-position_change):
                cc.send(ConsumerControlCode.VOLUME_DECREMENT)
        last_position = current_position

        if not back_switch.value:
            keyboard_mode = False
            current_menu = menu
            selected_index = 0
            show_menu()
            beep()