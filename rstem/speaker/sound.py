import os
import pygame.mixer
import pygame.sndarray
import pygame.time
import math
import numpy
import subprocess
import time

voice_engine = None

# global constants
SAMPLERATE = 48000
BITSIZE = -16  # unsigned 16 bit
CHANNELS = 2   # 1 == mono, 2 == stereo
BUFFER = 1024  # audio buffer size in no. of samples
FRAMERATE = 30 # how often to check if playback has finished

def _init():
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(SAMPLERATE, BITSIZE, CHANNELS, BUFFER)
        
def say(text, wait=True):
    proc = subprocess.Popen('espeak "' + text + '"', shell=True)
    if wait:
        proc.wait()
    
    
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
        
def shutdown():
    if pygame.mixer.get_init():
        pygame.mixer.quit()
    
    
    
class Sound(object):
    def __init__(self, filename):
        # initialize if the first time
        _init()
        # check if filename exists.. (pygame doesn't check)
        if not os.path.isfile(filename):
            raise IOError("Filename doesn't exist.")
        
        self.filename = filename
        self.sound = pygame.mixer.Sound(filename)
        
    def play(self, loops=0, wait=False):
        clock = pygame.time.Clock()
        self.sound.play(loops)
        if wait:
            while pygame.mixer.get_busy():
                clock.tick(FRAMERATE)
        
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

class Note(Sound):
    def __init__(self, frequency, amplitude=16000, duration=1):
        _init()
        self.filename = None
        self.frequency = frequency
        self.amplitude = amplitude
        self.duration = duration
        self.sound = pygame.sndarray.make_sound(self._build_samples())
        
    def _build_samples(self):
        num_steps = (self.duration/5.)*SAMPLERATE
        s = []
        for t in range(int(num_steps)):
            value = int(self.amplitude * math.sin(self.frequency * ((2 * math.pi)/SAMPLERATE) * t))
            s.append([value,value])
        x_arr = numpy.array(s)
        return x_arr
        
class Beep(Sound):
    # TODO: beep sounds came from here: http://www.soundjay.com/beep-sounds-1.html
    #  - need to find royalty free sounds that are allowed to be distributed
    def __init__(self, number=1):
        self.number = number
#        self.sound = Sound("beeps/beep-" + str(number) + ".wav")
        super(Beep, self).__init__("beeps/beep-" + str(number) + ".wav")

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
        
    def play(self, loops=0, start=0.0, wait=False):
        global currently_playing_file
        clock = pygame.time.Clock()
        # unpause if currently loaded
        if currently_playing_file == self.filename and pygame.mixer.music.get_busy():
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.load(self.filename)  # insert that tape deck
            pygame.mixer.music.play(loops, start)
            currently_playing_file = self.filename
            self.volume = pygame.mixer.music.get_volume()*100  # update volume

        if wait:
            while pygame.mixer.music.get_busy():
                clock.tick(FRAMERATE)
        
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
#    Note(440, duration=5).play()
    wiggle = Music("wiggle.mp3")
#    wiggle.play(wait=True)
    beep = Beep(2)
#    beep = Note(800)
    while 1:
        beep.set_volume(20)
        beep.play(wait=True)
        beep.set_volume(50)
        beep.play(wait=True)
    
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
        
        
        
