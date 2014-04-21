from subprocess import *

def get_data():
    pipe_out.write("6800")
    x = int(pipe_in.read(4), 16)
    pipe_out.write("7800")
    y = int(pipe_in.read(4), 16)
    return (x, y)

def _init_module():
    global pipe_in, pipe_out
    p = Popen("api/accel_server", shell=True, stdin=PIPE, stdout=PIPE)
    pipe_in = p.stdout
    pipe_out = p.stdin

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

_init_module()
if __name__ == "__main__":
    _main()

