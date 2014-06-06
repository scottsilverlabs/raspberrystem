#
# Copyright (c) 2014, Scott Silver Labs, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
from subprocess import *

def get_data():
    pipe_out.write("6800")
    x = int(pipe_in.read(4), 16)
    pipe_out.write("7800")
    y = int(pipe_in.read(4), 16)
    return (x, y)

def _init_module():
    global pipe_in, pipe_out
    here = os.path.dirname(os.path.realpath(__file__))
    p = Popen(here + "/accel_server", shell=True, stdin=PIPE, stdout=PIPE)
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

