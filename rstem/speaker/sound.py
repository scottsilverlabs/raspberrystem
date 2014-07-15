import os
import pygame.mixer
#import pyttsx
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
    proc = subprocess.Popen('espeak "' + text + '"', shell=True)
    proc.wait()
    
def tone(frequency=800, time=0.5):
    num_periods = frequency*time
    proc = subprocess.Popen('speaker-test  -f %f -r %f -t sine -p 0 -P %f -l 1 & P=$! && sleep' % (frequency, FREQ, num_periods), shell=True, stdout=subprocess.PIPE)
    proc.wait()
    
def beep(number=1):
    beep = Sound("/beeps/beep-" + number + ".wav")
    beep.play()
    
def get_volume():
    proc = subprocess.Popen('amixer sget Master', shell=True, stdout=subprocess.PIPE)
    amixer_stdout = proc.communicate()[0].split('\n')[4]
    proc.wait()
    find_start = amixer_stdout.find('[') + 1
    find_end = amixer_stdout.find('%]', find_start)
    return float(amixer_stdout[find_start:find_end])
    
def set_volume(value):
    value = float(int(value))
    proc = subprocess.Popen('amixer sset Master ' + str(value) + '%', shell=True, stdout=subprocess.PIPE)
    proc.wait()
    
def stop(background=True):
    """Stops all playback including background music unless background = False"""
    pygame.mixer.stop()
    if background:
        pygame.mixer.music.stop()
    
def pause(background=True):
    pygame.mixer.pause()
    if background:
        pygame.mixer.music.pause()
    
def play(background=True):
    pygame.mixer.unpause()
    if background:
        pygame.mixer.music.play()
    
    
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
        
    def stop(self):
        self.sound.stop()
        
    def get_volume(self):
        return self.sound.get_volume()*100
        
    def set_volume(self, value):
        if not (0 <= value <= 100):
            raise ValueError("Volume must be between 0 and 100.")
        self.sound.set_volume(float(value/100.))
        
    def get_length(self):
        return self.sound.get_length



currently_playing_file = None

class Music(Sound):
    
    def __init__(self, filename):
        # initialize if the first time
        _init()
        
        # check if filename exists.. (pygame doesn't check)
        if not os.path.isfile(filename):
            raise IOError("Filename doesn't exist.")
            
        self.filename = filename
        self.volume = None
        
    def play(self, loops=0, start=0.0):
        global currently_playing_file
        if currently_playing_file == self.filename and (pygame.mixer.music.get_busy()):
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.load(self.filename)
            pygame.mixer.music.play(loops, start)
            currently_playing_file = self.filename
            self.volume = pygame.mixer.music.get_volume()*100
        
    def queue(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.queue(self.filename)
        else:
            pygame.mixer.music.load(self.filename)
            
    def stop(self):
        if currently_playing_file == self.filename:
            pygame.mixer.music.stop()
        
    def pause(self):
        if currently_playing_file == self.filename:
            pygame.mixer.music.pause()
            
    def set_volume(self, value):
        if not (0 <= value <= 100):
            raise ValueError("Volume must be between 0 and 100.")
        self.volume = value
        if currently_playing_file == self.filename:
            pygame.mixer.music.set_volume(float(self.volume/100.))
        
    def get_volume(self):
        if self.volume is None:
            self.volume = pygame.mixer.music.get_volume()*100  # volume is set to default
        return self.volume
             
        
if __name__ == '__main__':
    tone()
#        say("Hello World")
#        say("How are you today?")
#        print(get_volume())
#        print("Playing wiggle.mp3")
#        wiggle = Music("wiggle.mp3")
#        wiggle.play()
#        time.sleep(10)
#        print("Background music volume is " + str(wiggle.get_volume()))
#        print("Playing 'front_center'")
#        fc = Sound("Front_Center.wav")
#        fc.play()
#        print("Sound volume is " + str(fc.get_volume()))
#        print("Master volume is " + str(get_volume()))
#        time.sleep(5)
#        print("Now play front_center again with volume down")
#        fc.set_volume(20)
#        fc.play()
#        time.sleep(1)
#        print("Turn background music down...")
##        set_volume(20)
#        wiggle.set_volume(20)
#        print("Volume: " + str(wiggle.get_volume()))
#        time.sleep(10)
#        print("Play that jazzy tune again!!! On infinite loop!! MUHAHAHA!!!")
#        wiggle.play(-1)
#        while 1:
#            pass
        
        
        
