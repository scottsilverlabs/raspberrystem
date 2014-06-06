import os
import accel_server
import atexit

@atexit.register
def cleanup():
    accel_server.closeSPI

class Accelerometer:
    
    def __init__(self):
        # TODO: set up spi stuff with accel_server
        global pipe_in, pipe_out
        here = os.path.dirname(os.path.realpath(__file__))
        p = Popen(here + "/accel_server", shell=True, stdin=PIPE, stdout=PIPE)
        pipe_in = p.stdout
        pipe_out = p.stdin

    def get_data():
        # TODO: use wrapped c function from accel_server
        pipe_out.write("6800")  # notify we want to receive x
        x = int(pipe_in.read(4), 16)
        pipe_out.write("7800")  # notify we want to receive y
        y = int(pipe_in.read(4), 16)
        
        return (x, y)

    def _main():
        import time
        import led

        xbase, ybase =  get_data()
        x, y = (4, 4)
        while True:
            xaccel, yaccel =  get_data()
            xchg = (xaccel - xbase)/20.0
            ychg = (yaccel - ybase)/20.0
            x, y = led.bound(x + xchg, y + ychg)

            led.erase()
            led.point(x, y)
            led.show()
            time.sleep(0.1);


