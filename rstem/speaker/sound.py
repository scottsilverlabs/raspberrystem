import os
import pygame.mixer
import pygame.sndarray
import pygame.time
import numpy
import subprocess
import time
import tempfile
import urllib2, urllib


# global constants
SAMPLERATE = 44100  # 38000 == chipmunks
BITSIZE = -16  # unsigned 16 bit
CHANNELS = 2   # 1 == mono, 2 == stereo
BUFFER = 1024  # audio buffer size in no. of samples
FRAMERATE = 30 # how often to check if playback has finished

# set of current talking process (used for is_talking())
talking_procs = set()

# engine used to create text to speech
voice_engine = None

def _init():
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(SAMPLERATE, BITSIZE, CHANNELS, BUFFER)
        
def is_talking():
    """
    @returns: True if speaker is currently saying text (from the L{say} function)
    @rtype: boolean
    """
    global talking_procs
    for proc in talking_procs:
        if proc.poll() is None:  # if proc.poll() gives us a returncode, its terminated
            return True
    return False  # all processes were terminated, therefore not talking
        
        
def set_voice_engine(engine="espeak"):
    """Set voice engine and do and intial configures if necessary"""
    global voice_engine
    if engine == "espeak":
        # check if espeak is installed
        proc = subprocess.Popen('dpkg-query -s espeak', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = proc.communicate()
        if output.find("install ok installed") == -1:
            raise Exception("espeak is not installed")
        voice_engine = "espeak"
        
    elif engine == "google":
        voice_engine = "google"
    else:
        raise ValueError("Voice Engine is not supported.")

    
def say(text, wait=False):    
    
    # check if espeak is installed
    proc = subprocess.Popen('dpkg-query -s espeak', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = proc.communicate()
    if output.find("install ok installed") == -1:
        raise Exception("espeak is not installed")
    proc = subprocess.Popen('espeak -s 200 "' + text + '"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if wait:
        proc.wait()
    else:
        global talking_procs
        talking_procs.add(proc)
    
def get_volume():
    """Gets the master volume"""
    proc = subprocess.Popen('amixer sget Master', shell=True, stdout=subprocess.PIPE)
    amixer_stdout = proc.communicate()[0].split('\n')[4]
    proc.wait()
    find_start = amixer_stdout.find('[') + 1
    find_end = amixer_stdout.find('%]', find_start)
    return float(amixer_stdout[find_start:find_end])
    
def set_volume(value):
    """Set the master volume"""
    value = float(int(value))
    proc = subprocess.Popen('amixer sset Master ' + str(value) + '%', shell=True, stdout=subprocess.PIPE)
    proc.wait()
    
def stop(background=True):
    """Stops all playback including background music unless background = False"""
    pygame.mixer.stop()
    if background:
        pygame.mixer.music.stop()
    
def pause(background=True):
    """Pauses all playback including background music unless background = False"""
    pygame.mixer.pause()
    if background:
        pygame.mixer.music.pause()
    
def play(background=True):
    """Unpauses all playback including background music unless background = False"""
    pygame.mixer.unpause()
    if background:
        pygame.mixer.music.unpause()
        
def shutdown():
    """Clean up initialization"""
    if pygame.mixer.get_init():
        pygame.mixer.quit()
    
currently_playing_filename = None

class Sound(object):
    """Basic foreground sound from a file"""
    def __init__(self, filename, background=False):
        # initialize if the first time
        _init()
        # check if filename exists.. (pygame doesn't check)
        if not os.path.isfile(filename):
            raise IOError("Filename doesn't exist.")
        
        self.background = background
        self.filename = filename
        self.channel = None
        if background:
            self.sound = pygame.mixer.music
        else:
            self.sound = pygame.mixer.Sound(filename)
        
    def play(self, loops=0, wait=False):
        """Plays sound a certain number of times. Blocks if wait == True"""
        global currently_playing_filename
        if self.background and currently_playing_filename != self.filename:
            self.sound.load(self.filename)
            currently_playing_filename = self.filename
        
        self.channel = self.sound.play(loops)
        if wait:
            clock = pygame.time.Clock()
            if self.background:
                while pygame.mixer.music.get_busy():
                    clock.tick(FRAMERATE)
            else:
                while pygame.mixer.get_busy():
                    clock.tick(FRAMERATE)               
                
    def stop(self):
        if self.background and currently_playing_filename != self.filename:
            return
        self.sound.stop()
        self.channel = None
        
    def get_duration(self):
        if not self.background:
            return self.sound.get_length()
        else:
            # temporarily load file as a sound to check
            temp_sound = pygame.mixer.Sound(self.filename)
            return temp_sound.get_length()
        
    def get_volume(self):
        """Gets the volume of individual sound"""
        return self.sound.get_volume()*100
        
    def set_volume(self, value):
        if self.background and currently_playing_filename != self.filename:
            return
        """Sets teh volume of individual sound"""
        if not (0 <= value <= 100):
            raise ValueError("Volume must be between 0 and 100.")
        self.sound.set_volume(float(value/100.))
        
    def is_playing(self):
        if self.background and currently_playing_filename != self.filename:
            return False
        if self.background:
            return self.sound.get_busy()
        else:
            if self.channel is not None:
                return self.channel.get_busy()
            else:
                return False
        
    def queue(self):
        if not self.background:
            raise ValueError("Queue only supports background sounds.")
        pygame.mixer.music.queue(self.filename)
        
class Speech(Sound):

    def __init__(self, text):
        # setup voice engine to default espeak if not set up
        if voice_engine is None:
            set_voice_engine()
            
        # initialize pygame
        _init()

        # create temp file to use
        self.filename = tempfile.mkstemp(suffix=".mp3")[1]
        self.background = False
        
        # create wav file of the text, using voice_engine
        if voice_engine == "espeak":
            proc = subprocess.Popen('espeak "' + text + '" -w ' + self.filename, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            if len(error) > 0:
                raise IOError(error)
            self.sound = pygame.mixer.Sound(self.filename)
            
        elif voice_engine == "google":
            text = urllib.quote(text)
            url = 'http://translate.google.com/translate_tts?tl=en&q=' + text
            print url
            req = urllib2.Request(url)
            print "Made request"
            req.add_header('User-Agent', 'Konqueror')
            print "Added header"
            print self.filename
            fp = open(self.filename, 'wb')
            try:
                response = urllib2.urlopen(req)
                print "opened url"
                fp.write(response.read())
                print "read it"
                time.sleep(.5)
            except urllib2.URLError as e:
                print ('%s' % e)
            fp.close()
            
            self.sound = pygame.mixer.Sound(self.filename)


class Note(Sound):
    """Creates a sine wave of given frequeny"""
    def __init__(self, frequency, amplitude=100, duration=1):
        _init()
        self.filename = None
        self.background = False
        self.frequency = frequency
        self.amplitude = amplitude
        self.duration = duration
        
        length = 2*SAMPLERATE/float(frequency)
        omega = numpy.pi * 2 / length
        xvalues = numpy.arange(int(length)) * omega
        array = numpy.array(amplitude * numpy.sin(xvalues), dtype="int8")
        array = numpy.resize(array, (SAMPLERATE*duration,))
        if CHANNELS == 2:
            array = numpy.array(zip(array,array))  # split into two for stereo
        self.sound = pygame.sndarray.make_sound(array)
        
        
if __name__ == '__main__':
#    Note(440, duration=5).play()
    wiggle = Sound("wiggle.mp3", background=True)
#    wiggle.play(wait=True)
    beep = Note(440, duration=5)
    beep.play(0, wait=True)
#    while 1:
#        for j in range(0,100,5):
#            set_volume(j)
##            for i in range(10):
#            beep.set_volume(20)
#            beep.play(wait=True)
#            beep.set_volume(50)
#            beep.play(wait=True)
#        for j in range(100,-1,-5):
#            set_volume(j)
##            for i in range(10):
#            beep.set_volume(20)
#            beep.play(wait=True)
#            beep.set_volume(50)
#            beep.play(wait=True)
    
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
        
        
        
