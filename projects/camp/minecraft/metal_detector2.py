from rstem.mcpi import minecraft, control, block
from rstem.sound import Note
import time
from random import randint
from math import log

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()

beep = Note('A5')
BEEP_DURATION = 0.05

ARENA_WIDTH = 10
GOLD_DEPTH = 2
gold_pos = mc.player.getTilePos()
gold_pos.x +=  randint(-ARENA_WIDTH, ARENA_WIDTH)
gold_pos.z +=  randint(-ARENA_WIDTH, ARENA_WIDTH)
gold_pos.y = mc.getHeight(gold_pos.x, gold_pos.z) - GOLD_DEPTH
mc.setBlock(gold_pos, block.GOLD_BLOCK)

next_beep_time = time.time()
while block.Block(mc.getBlock(gold_pos)) == block.GOLD_BLOCK:
    player_pos = mc.player.getTilePos()
    vector_to_gold = gold_pos - player_pos
    vector_to_gold.y = 0
    distance_to_gold = vector_to_gold.length()

    if time.time() > next_beep_time:
        if distance_to_gold <= 1:
            if not beep.is_playing():
                beep.play(duration=None)
        else:
            beep.play(duration=BEEP_DURATION).wait()
            next_beep_time = time.time() + log(distance_to_gold/100 + 1)
    
    time.sleep(0.01)

beep.stop()
mc.postToChat("You found the gold!")
time.sleep(3)


