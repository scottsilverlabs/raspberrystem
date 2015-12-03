from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
from rstem.led_matrix import FrameBuffer, Sprite
from itertools import cycle
import time

fb = FrameBuffer()

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()

animation = [
    Sprite("""
        00000000
        0000FF00
        000FF000
        000FFF00
        00FFFF00
        000FFF00
        0FF00F00
        0F0000FF
        """),
    Sprite("""
        00000000
        0000FF00
        0000F000
        00FFFF00
        0F0FF0F0
        000FFF00
        0FF00F00
        00000FF0
        """),
    Sprite("""
        00000000
        0000FF00
        000FF000
        000FF000
        000FF000
        000FF000
        00FFF000
        000FF000
        """),
    Sprite("""
        0000FF00
        000FF000
        000FFF00
        00FFFF00
        000FFF00
        00F00F00
        00F0F000
        00F00000
        """),
    ]


def sprite_in_minecraft(mc, sprite, pos):
    char_sprite = reversed(str(sprite).splitlines())
    for height, row in enumerate(char_sprite):
        for width, char in enumerate(row):
                if char == '0':
                    blk = block.AIR
                else:
                    blk = block.WOOD
                mc.setBlock(player_pos + Vec3(width, height, 0), blk)
    
player_pos = mc.player.getTilePos()
animation = cycle(animation)
while True:
    sprite = next(animation)

    fb.erase()
    fb.draw(sprite)
    fb.show()

    sprite_in_minecraft(mc, sprite, player_pos)

    time.sleep(0.1)

