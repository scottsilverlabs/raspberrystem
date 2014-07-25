from rstem import led_matrix
import RPi.GPIO as GPIO
import subprocess
import os
import sys
import time

class Menu(object):
    def __init__(self, menu_items):
        items = []
        # convert titles
        for i, item in enumerate(menu_items):
            f = os.path.abspath(item[1])
            if not os.path.isfile(f):
                raise IOError("File '" + f + "' could not be found.")
            items.append({
                "title": item[0], 
                "file": f,
                "text": led_matrix.LEDText(item[0])
#                "inverted": False
                })
        self.items = items
        self.running_proc = None
        
        # set first item to be selected
#        items[0]["inverted"] = True
#        items[0]["text"].invert()
        
    def draw(self):
        # display menu items
        pos_y = 0
        for item in self.items:
            if pos_y >= led_matrix.height():
                break
#            if item["inverted"]:
#                # display text inverted
#                led_matrix.rect((0, pos_y), (led_matrix.width(), item["text"].height))
#                led_matrix.text(item["text"], (0, pos_y), color=0)
#            else:
            led_matrix.text(item["text"], (0, pos_y))
            pos_y += item["text"].height + 1
    
    def _rotate(self, n):
        """Rotates counterclockwise if positive, clockwise if negative"""
        l = self.items
        self.items = l[n:] + l[:n]
    
    def scroll_up(self):
#        self.items[0]["inverted"] = False
#        self.items[0]["text"].invert()  # un-invert old selected item
        self._rotate(1)
#        self.items[0]["text"].invert()  # invert new selected item
#        self.items[0]["inverted"] = True
        
    def scroll_down(self):
#        self.items[0]["inverted"] = False
#        self.items[0]["text"].invert()  # un-invert old selected item
        self._rotate(-1)
#        self.items[0]["text"].invert()  # invert new selected item
#        self.items[0]["inverted"] = True
    
    def selected_item(self):
        """Returns selected item, which should be first inverted item."""
        return self.items[0]
#        for item in self.items:
#            if item["inverted"]:
#                return item
                
    def run_selected_item(self):
        selected = self.selected_item()
#        exec(open(selected["file"]).read())
        proc = subprocess.Popen([sys.executable, selected["file"], selected["title"]])
        self.running_proc = proc
        
    def terminate_running_item(self):
        if self.running_proc is not None:
            self.running_proc.terminate()
            self.running_proc.wait()
            self.running_proc = None
    
# set up menu
menu_items = [
    ["Protector", "protector.py"],
    ["Stack-em", "stackem.py"]
]
menu = Menu(menu_items)

# setup buttons
SELECT = 4
# TODO: set these to real values
UP = 18
DOWN = 23
# buttons to hold down at the same time to kill running process
KILL_SWITCH_COMBO = [UP, DOWN, SELECT]

# states
IN_MENU = 1
IN_GAME = 2
curr_state = IN_MENU

def button_handler(channel):
    if channel == SELECT:
        global curr_state
        curr_state = IN_GAME
        menu.run_selected_item()
    elif channel == UP:
        menu.scroll_up()
    elif channel == DOWN:
        menu.scroll_down()

# initialization
led_matrix.init_grid(1,2,math_coords=False)
GPIO.setmode(GPIO.BCM)
for button in [SELECT, UP, DOWN]:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=300)


while True:
    if curr_state == IN_MENU:
#        print ("IN_MENU")
        led_matrix.erase()
#        led_matrix.text("hello")
        menu.draw()
        led_matrix.show()
#        time.sleep(1)
    elif curr_state == IN_GAME:
        print("IN_GAME")
        if all([not bool(GPIO.input(button)) for button in KILL_SWITCH_COMBO]):
            menu.terminate_running_item()
            curr_state = IN_MENU
    
    
