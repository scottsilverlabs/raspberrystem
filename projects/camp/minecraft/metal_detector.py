from rstem.mcpi import minecraft, control, block
import time
from random import randint

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()

ARENA_WIDTH = 3
GOLD_DEPTH = 0
gold_pos = mc.player.getTilePos()
gold_pos.x +=  randint(-ARENA_WIDTH, ARENA_WIDTH)
gold_pos.z +=  randint(-ARENA_WIDTH, ARENA_WIDTH)
gold_pos.y = mc.getHeight(gold_pos.x, gold_pos.z) - GOLD_DEPTH
mc.setBlock(gold_pos, block.GOLD_BLOCK)
gold_exists = True

while gold_exists:
    player_pos = mc.player.getTilePos()
    gold_exists = block.Block(mc.getBlock(gold_pos)) == block.GOLD_BLOCK
    time.sleep(0.01)

mc.postToChat("You found the gold!")
time.sleep(3)


