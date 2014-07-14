import os

import pygame.mixer
pygame.mixer.init()

initialized = False

# global constants
FREQ = 48000
BITSIZE = -16  # unsigned 16 bit
CHANNELS = 2   # 1 == mono, 2 == stereo
BUFFER = 1024  # audio buffer size in no. of samples
FRAMERATE = 30 # how often to check if playback has finished

def init():
    global initialized
    if not initialized:
        pygame.mixer.init(FREQ, BITSIZE, CHANNELS, BUFFER)
        initialized = True
        

class Sound(object):
    
    def __init__(self, filename):
        # initialize if the first time
        init()
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
        init()
        
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
        
        
        
        
        
        
        
        
        
        
        
        
