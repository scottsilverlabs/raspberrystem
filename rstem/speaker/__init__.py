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
import pygame.mixer
import pygame.sndarray
import pygame.time
import math
import numpy
import subprocess
import time

voice_engine = None

# global constants
SAMPLERATE = 44100  # 38000 == chipmunks
BITSIZE = -16  # unsigned 16 bit
CHANNELS = 2   # 1 == mono, 2 == stereo
BUFFER = 1024  # audio buffer size in no. of samples
FRAMERATE = 30 # how often to check if playback has finished

def _init():
    """Initializes pygame"""
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(SAMPLERATE, BITSIZE, CHANNELS, BUFFER)
        
def say(text):
    """Plays a voice speaking the given text.
    
    @param text: text to play
    @type text: string
    
    @raise Exception: espeak errors out (most likely due to not being installed)
    @note: Must have espeak installed
    """
    proc = subprocess.Popen('espeak "' + text + '"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = proc.communicate()
    if len(error) > 0:
        raise Exception(error)
    
def get_volume():
    """Gets the master volume
    
    @rtype: float
    @returns: the volume between 0-100
    """
    proc = subprocess.Popen('amixer sget Master', shell=True, stdout=subprocess.PIPE)
    amixer_stdout = proc.communicate()[0].split('\n')[4]
    proc.wait()
    find_start = amixer_stdout.find('[') + 1
    find_end = amixer_stdout.find('%]', find_start)
    return float(amixer_stdout[find_start:find_end])
    
def set_volume(value):
    """Set the master volume
    
    @param value: Volume to set (must be between 0-100)
    @type value: int
    """
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
        
def cleanup():
    """Cleans up initialization of pygame"""
    if pygame.mixer.get_init():
        pygame.mixer.quit()
    
currently_playing_filename = None

class Sound(object):
    """Basic foreground or background sound from a file"""
    def __init__(self, filename, background=False):
        """
        @param filename: Relative path to sound file
        @type filename: string
        @param background: Whether to play the sound as background music or as a sound effect
        @type background: boolean
        """
        # initialize if the first time
        _init()
        # check if filename exists.. (pygame doesn't check)
        if not os.path.isfile(filename):
            raise IOError("Filename doesn't exist.")
        
        self.background = background
        self.filename = filename
        if background:
            self.sound = pygame.mixer.music
        else:
            self.sound = pygame.mixer.Sound(filename)
        
    def play(self, loops=0, wait=False):
        """Plays sound a certain number of times
        @param loops: number of loops to play the sound (-1 to play infinitly)
        @type loops: int
        @param wait: If true, blocks until playback is finished
        @type wait: boolean
        """
        global currently_playing_filename
        if self.background and currently_playing_filename != self.filename:
            self.sound.load(self.filename)
            currently_playing_filename = self.filename
        
        clock = pygame.time.Clock()
        self.sound.play(loops)
        if wait:
            if self.background:
                while pygame.mixer.music.get_busy():
                    clock.tick(FRAMERATE)
            else:
                while pygame.mixer.get_busy():
                    clock.tick(FRAMERATE)               
                
    def stop(self):
        """Stops playback of sound."""
        if self.background and currently_playing_filename != self.filename:
            return
        self.sound.stop()
        
    def get_volume(self):
        """Gets the volume of individual sound
        @returns: volume (a value between 0-100)
        @rtype: int
        """
        return self.sound.get_volume()*100
        
    def set_volume(self, value):
        """Sets the volume of given sound.
        @param value: volume to set sound at (between 0-100)
        @type value: int
        """
        if self.background and currently_playing_filename != self.filename:
            return
        """Sets teh volume of individual sound"""
        if not (0 <= value <= 100):
            raise ValueError("Volume must be between 0 and 100.")
        self.sound.set_volume(float(value/100.))
        
    def is_playing(self):
        """
        @returns: True if sound is currently playing
        @rtype: boolean
        """
        if self.background and currently_playing_filename != self.filename:
            return False
        self.sound.get_busy()
        
    def queue(self):
        """Queues sound to play after other queued sounds have finished playing.
        @raises ValueError: Sounds is not a background sound. (Only supports background music)
        """
        if not self.background:
            raise ValueError("Queue only supports background sounds.")
        pygame.mixer.music.queue(self.filename)
        

class Note(Sound):
    """A sine wave of given frequeny"""
    def __init__(self, frequency, amplitude=100, duration=1):
        """
        @param frequency: frequency of the sine wave in Hz
        @type frequency: float or int
        @param amplitude: amplitude of the sine wave
        @type amplitude: float or int
        @param duration: length of sine wave in seconds
        @type duration: float or int
        """
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
        
        
        
