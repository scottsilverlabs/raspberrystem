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
        def seek(self, position, absolute=False, percentage=False)
            - relative +/- seconds
            - absolute +/- seconds (-negative seconds from end)
            - absolute percentage
            - returns previous position, in seconds
    class Speech(Sound):
        def __init__(self, text):
    class Note(Sound):
        def __init__(self, pitch):
'''

TEST_SOUND='/home/pi/python_games/match1.wav'
TEST_SOUND_LENGTH=0.565125
TEST_SOUND_LONG='/usr/share/scratch/Media/Sounds/Music Loops/Techno2.mp3'
TEST_SOUND_LONG_LENGTH=14.837551

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

@testing.automatic
def sound_wait():
    s = Sound(TEST_SOUND)
    s.play()
    s.wait()
    return not s.is_playing()

@testing.automatic
def sound_stop():
    s = Sound(TEST_SOUND)
    s.play()
    s.stop()
    return not s.is_playing()

@testing.automatic
def sound_playing_before_end_of_duration_play():
    s = Sound(TEST_SOUND_LONG)
    s.play(duration=1.0)
    time.sleep(0.5)
    playing = s.is_playing()
    s.stop()
    return playing

@testing.automatic
def sound_not_playing_after_end_of_duration_play():
    s = Sound(TEST_SOUND_LONG)
    s.play(duration=1.0)
    time.sleep(1.5)
    return not s.is_playing()

@testing.automatic
def sound_playing_before_end_of_negative_duration_play():
    s = Sound(TEST_SOUND_LONG)
    s.play(duration=(1.0-TEST_SOUND_LONG_LENGTH))
    time.sleep(0.5)
    playing = s.is_playing()
    s.stop()
    return playing

@testing.automatic
def sound_not_playing_after_end_of_negative_duration_play():
    s = Sound(TEST_SOUND_LONG)
    s.play(duration=(1.0-TEST_SOUND_LONG_LENGTH))
    time.sleep(1.5)
    return not s.is_playing()

@testing.automatic
def sound_playing_before_end_of_2_loops():
    s = Sound(TEST_SOUND)
    s.play(loops=2)
    time.sleep(TEST_SOUND_LENGTH * 2 - 0.5)
    playing = s.is_playing()
    s.stop()
    return playing

@testing.automatic
def sound_not_playing_after_end_of_2_loops():
    s = Sound(TEST_SOUND)
    s.play(loops=2)
    time.sleep(TEST_SOUND_LENGTH * 2 + 0.5)
    playing = s.is_playing()
    s.stop()
    return not playing

@testing.automatic
def sound_playing_before_end_of_2_loops_of_fixed_duration():
    s = Sound(TEST_SOUND_LONG)
    s.play(duration=1.0, loops=2)
    playing = s.is_playing()
    s.stop()
    return playing

@testing.automatic
def sound_not_playing_after_end_of_2_loops_of_fixed_duration():
    s = Sound(TEST_SOUND_LONG)
    s.play(duration=1.0, loops=2)
    time.sleep(2.5)
    playing = s.is_playing()
    s.stop()
    return not playing

@testing.automatic
def sound_play_then_replay():
    return False

@testing.automatic
def sound_get_set_volume():
    # Verify Sound volume attribute can be get/set.
    return False

@testing.manual_output
def sound_play_test_sound():
    '''The sound match1.wav will play on the speaker (about 0.5 seconds).'''
    Sound(TEST_SOUND).play()

@testing.manual_output
def sound_play_test_sound_loop_2():
    '''The sound match1.wav will play TWO TIMES on the speaker (about 0.5 seconds each).'''
    Sound(TEST_SOUND).play(loops=2)

@testing.manual_output
def sound_master_volume():
    '''The sound match1.wav will play on the speaker 5 times (about 0.5 seconds
    each), at 20, 40, 60, 80 and 100% master volume.
    '''
    raise Exception()

@testing.manual_output
def sound_sound_volume():
    '''The sound match1.wav will play on the speaker 5 times (about 0.5 seconds
    each), at 20, 40, 60, 80 and 100% volume.
    '''
    raise Exception()

