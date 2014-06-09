import os
import accel_server
import time
import atexit
import math

@atexit.register
def cleanup():
    accel_server.closeSPI()

class Accelerometer:
    
    def __init__(self):
        # TODO: provide chip select port and control chip select port?
        accel_server.initSPI(500000)
        self.callibrate()
#        global pipe_in, pipe_out
#        here = os.path.dirname(os.path.realpath(__file__))
#        p = Popen(here + "/accel_server", shell=True, stdin=PIPE, stdout=PIPE)
#        pipe_in = p.stdout
#        pipe_out = p.stdin

    def get_data(self):
        # write first and second byte to MCP3002 to get channel 0
        x1 = accel_server.write(int('01101000',2))
        x2 = accel_server.write(0)
        x = ((x1 & 0xFF) << 4) | (x2 & 0xFF)
        
        # write first and second byte to MCP3002 to get channel 1
        y1 = accel_server.write(int('01111000',2))
        y2 = accel_server.write(0)
        y = ((y1 & 0xFF) << 4) | (y2 & 0xFF)
    
        return (x, y)
        
#        pipe_out.write("6800")  # notify we want to receive x
#        x = int(pipe_in.read(4), 16)
#        pipe_out.write("7800")  # notify we want to receive y
#        y = int(pipe_in.read(4), 16)
#        
#        return (x, y)

    def get_angles(self):
        # TODO: fix to get right numbers
        x, y = self.get_data()
        return (asin(x - self.x_base), asin(y - self.y_base))
    
    def callibrate(self):
        x, y = self.get_data()
        self.x_base = x
        self.y_base = y
        

    def _main(self):
        x, y = self.get_data()
        
        print "x = " + str(x) + "   y = " + str(y)
        
        
#        import time
#        import led
        
#        xbase, ybase =  get_data()
#        x, y = (4, 4)
#        while True:
#            xaccel, yaccel =  get_data()
#            xchg = (xaccel - xbase)/20.0
#            ychg = (yaccel - ybase)/20.0
#            x, y = led.bound(x + xchg, y + ychg)

#            led.erase()
#            led.point(x, y)
#            led.show()
#            time.sleep(0.1);

if __name__ == "__main__":
    accel = Accelerometer()
    while 1:
        accel._main()
        time.sleep(1)


