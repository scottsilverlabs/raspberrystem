from rstem.mcpi import minecraft, vec3, block
from rstem.mcpi import control
from math import atan2, degrees
import time


def wait_until_stopped(mc):
    prev = None
    cur = mc.player.getPos()
    while cur != prev:
        prev = cur
        cur = mc.player.getPos()
        time.sleep(0.05)
    return cur

def make_platform(mc, erase=False, height=60, half_width=3):
    if erase:
        bottom_block = block.AIR
        top_block = block.AIR
    else:
        bottom_block = block.BRICK_BLOCK
        top_block = block.COBWEB

    mc.setBlocks(
        vec3.Vec3(-half_width, height, -half_width), 
        vec3.Vec3(half_width, height, half_width), 
        bottom_block)
    mc.setBlocks(
        vec3.Vec3(-half_width, height+1, -half_width), 
        vec3.Vec3(half_width, height+3, half_width), 
        top_block)

    return vec3.Vec3(0, height+1, 0)

def get_direction_simple(mc):
    original_pos = mc.player.getPos()
    control.forward(0.1)
    time.sleep(1)
    end = mc.player.getPos()

    mc.player.setPos(original_pos)

    angle_to_z = degrees(atan2((end.x - original_pos.x),(end.z - original_pos.z)))
    return angle_to_z

def get_direction(mc):
    original_pos = mc.player.getPos()
    center_of_platform = make_platform(mc)
    mc.player.setPos(center_of_platform)
    control.forward(0.1)
    end = wait_until_stopped(mc)
    make_platform(mc, erase=True)

    mc.player.setPos(original_pos)

    angle_to_z = degrees(atan2((end.x - center_of_platform.x),(end.z - center_of_platform.z)))
    return angle_to_z

mc = minecraft.Minecraft.create()
start = time.time()
direction = get_direction(mc)
print(time.time()-start)
print(direction)
