import testing_log
import importlib
import testing
import time
from threading import Timer
from functools import wraps

from rstem.sound import Sound, Sox

'''
Tests of sound module

Manual tests require a speaker attached to the the audio jack (with or without
speaker amplifier).
'''

'''
    class Sound(object):
        def play(self, loop=1, duration=None):
            - play when already playing kills and restarts
            - postive duration ralative to current seek, negative duration relative to end of clip
        def seek(self, position, seek_absolute=False, seek_percentage=False)
            - relative +/- seconds
            - absolute +/- seconds (-negative seconds from end)
            - absolute percentage
            - returns previous position, in seconds
        def stop(self):
        volume attribute
        def wait(self):
        def is_playing(self):
        staticmethod:
            master volume
    class Speech(Sound):
        def __init__(self, text):
    class Note(Sound):
        def __init__(self, pitch):
'''

TEST_SOUND='/home/pi/python_games/match1.wav'
TEST_SOUND_LENGTH=0.565125

@testing.automatic
def sound_init_with_known_good_sound():
    s = Sound(TEST_SOUND)
    return isinstance(s, Sound)

@testing.automatic
def sound_length():
    return Sound(TEST_SOUND).length() == TEST_SOUND_LENGTH

@testing.automatic
def sound_init_bad_filename():
    try:
        s = Sound("qwemceqwncklenqwc")
    except IOError:
        return True
    return False

@testing.automatic
def sound_init_bad_filename_2():
    try:
        s = Sound([1,2,3])
    except TypeError:
        return True
    return False

@testing.automatic
def sound_not_is_playing_before_play():
    s = Sound(TEST_SOUND)
    return not s.is_playing()

@testing.automatic
def sound_not_is_playing_after_play():
    s = Sound(TEST_SOUND)
    s.play()
    time.sleep(TEST_SOUND_LENGTH + 0.5)
    return not s.is_playing()

@testing.automatic
def sound_is_playing_at_play_start():
    s = Sound(TEST_SOUND)
    s.play()
    return s.is_playing()

@testing.automatic
def sound_is_playing_at_play_middle():
    s = Sound(TEST_SOUND)
    s.play()
    time.sleep(TEST_SOUND_LENGTH/2)
    return s.is_playing()

@testing.manual_output
def sound_play_test_sound():
    '''The sound match1.wav will play on the speaker (about 0.5 seconds)
    '''
    try:
        s = Sound(TEST_SOUND)
        s.play()
    except ValueError:
        return True
    return False
