import os
import pygame.mixer
import pyttsx
import subprocess
import time

initialized = False
voice_engine = None

# global constants
FREQ = 48000
BITSIZE = -16  # unsigned 16 bit
CHANNELS = 2   # 1 == mono, 2 == stereo
BUFFER = 1024  # audio buffer size in no. of samples
FRAMERATE = 30 # how often to check if playback has finished

def _init():
    global initialized
    if not initialized:
        pygame.mixer.init(FREQ, BITSIZE, CHANNELS, BUFFER)
        initialized = True
        
def say(text):
    global voice_engine
#    if voice_engine is None:
    voice_engine = pyttsx.init()
    voice_engine.say(text)
    voice_engine.runAndWait()
#    else:
#        print("here")
#        voice_engine.say(text)

    
def get_volume():
    proc = subprocess.Popen('amixer sget Master', shell=True, stdout=subprocess.PIPE)
    amixer_stdout = proc.comunicate()[0].split('\n')[4]
    proc.wait()
    find_start = amixer_stdout.find('[') + 1
    find_end = amixer_stdout.find('%]', find_start)
    
    return float(amixer_stdout[find_start:find_end])
    
def set_volume(value):
    value = float(int(value))
    proc = subprocess.Popen('amixer sset Master ' + str(value) + '%', shell=True, stdout=subprocess.PIPE)
    proc.wait()
    
    
class Sound(object):
    
    def __init__(self, filename):
        # initialize if the first time
        _init()
        # check if filename exists.. (pygame doesn't check)
        if not os.path.isfile(filename):
            raise IOError("Filename doesn't exist.")
        
        self.filename = filename
        self.sound = pygame.mixer.Sound(filename)
        
    def play(self):
        self.sound.play()

class Music(Sound):
    
    def __init__(self, filename):
        # initialize if the first time
        _init()
        
        # check if filename exists.. (pygame doesn't check)
        if not os.path.isfile(filename):
            raise IOError("Filename doesn't exist.")
            
        sound.filename = filename
        
        
    def play(self):
        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.play()
        
    def queue(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.queue(self.filename)
            
    def set_volume(value):
        pygame.mixer.music.set_volume(value)
        
        
if __name__ == '__main__':
        say("Hello World")
        say("How are you today?")
        time.sleep(2)
        
        
        
        
        
        
