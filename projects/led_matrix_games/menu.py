from rstem import led_matrix
import RPi.GPIO as GPIO
import subprocess
import os
import sys
import time
import signal

class Menu(object):

    HOLD_CLOCK_TIME = -30 # number of cycles to hold scrolling text
    
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
#        self.running_proc = None
        self.scrolling_text_pos = 0
        self.scrolling_text_clock = Menu.HOLD_CLOCK_TIME  # clock used to slow down scrolling text
        self.scrolling_text_cycle = 5  # number of cycles between scrolling tick
        
        # set first item to be selected
#        items[0]["inverted"] = True
#        items[0]["text"].invert()
        
    def draw(self):
        # display menu items
        pos_y = 0
        selected_item = self.selected_item()
        
        # display all other items regularly
        for item in self.items:
            if pos_y >= led_matrix.height():
                break

            if item["title"] == selected_item["title"]:
                # display selected text scrolling
                x = self.scrolling_text_pos
                led_matrix.text(selected_item["text"], (x, pos_y))
                if self.scrolling_text_clock == self.scrolling_text_cycle:
                    self.scrolling_text_clock = 0
                    if self.scrolling_text_pos < -selected_item["text"].width:
                        self.scrolling_text_pos = led_matrix.width() - 1
                    else:
                        self.scrolling_text_pos -= 1
                self.scrolling_text_clock += 1
#            if item["inverted"]:
#                # display text inverted
#                led_matrix.rect((0, pos_y), (led_matrix.width(), item["text"].height))
#                led_matrix.text(item["text"], (0, pos_y), color=0)
#            else:
            else:
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
        self.scrolling_text_pos = 0
        self.scrolling_text_clock = Menu.HOLD_CLOCK_TIME
#        self.items[0]["text"].invert()  # invert new selected item
#        self.items[0]["inverted"] = True
        
    def scroll_down(self):
#        self.items[0]["inverted"] = False
#        self.items[0]["text"].invert()  # un-invert old selected item
        self._rotate(-1)
        self.scrolling_text_pos = 0
        self.scrolling_text_clock = Menu.HOLD_CLOCK_TIME
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
        cleanup()
        proc = subprocess.Popen(
            [sys.executable, selected["file"], selected["title"]],
#            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            )
        output, error = proc.communicate() # wait for process to terminate
        if error:
            raise RuntimeError(error)
        setup()  # resetup
#        self.running_proc = proc
#        self.terminate_running_item()
        
#    def terminate_running_item(self):
#        if self.running_proc is not None:
#            self.running_proc.terminate()
#            self.running_proc.wait()
#            self.running_proc = None
    
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
#        led_matrix.shutdown_matrices()
#        menu.run_selected_item()
    elif channel == UP:
        menu.scroll_up()
    elif channel == DOWN:
        menu.scroll_down()

def setup():
    led_matrix.init_grid(1,2,math_coords=False)
    GPIO.setmode(GPIO.BCM)
    for button in [SELECT, UP, DOWN]:
        GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=300)
        
def cleanup():
    led_matrix.shutdown_matrices()
    GPIO.cleanup()

# clean up code
def exits(*args):
    print("Exiting")
    menu.terminate_running_item()
    led_matrix.shutdown_matrices()
    GPIO.cleanup()
    sys.exit(0)
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


setup()
while True:
    if curr_state == IN_MENU:
#        print(menu.items)
        led_matrix.erase()
        menu.draw()
        led_matrix.show()
    elif curr_state == IN_GAME:
        menu.run_selected_item()  # run game and wait for it to die
        curr_state = IN_MENU
#        if all([not bool(GPIO.input(button)) for button in KILL_SWITCH_COMBO]):
#            print("KILL_SWITCH_COMBO")
#            menu.terminate_running_item()
#            led_matrix.init_grid(1,2,math_coords=False)
#            curr_state = IN_MENU
#            time.sleep(5) # allow for time 
    
    
