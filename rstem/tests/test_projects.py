'''
Tests of projects

Requires projects lid
'''
import traceback
import testing
import sys

@testing.manual_io
def piano_app():
    '''Piano app
    '''
    sys.path.append('../../projects/camp/piano')
    import piano9

@testing.manual_io
def space_invaders_app():
    '''Piano app
    '''
    sys.path.append('../../projects/camp/space_invaders')
    import space_invaders9

@testing.manual_io
def simon_app():
    '''Piano app
    '''
    sys.path.append('../../projects/camp/simon')
    import simon9

