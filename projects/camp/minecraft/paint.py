from rstem.button import Button
from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
import time

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()

left = Button(23)
right = Button(14)
up = Button(18)
down = Button(15)

cursor = mc.player.getTilePos()
cursor.y = mc.getHeight(cursor.x, cursor.z)

while True:
    old_cursor = cursor.clone()
    cursor += Vec3(0, 0, right.presses())
    cursor += Vec3(0, 0, -left.presses())
    cursor += Vec3(up.presses(), 0, 0)
    cursor += Vec3(-down.presses(), 0, 0)
    if old_cursor != cursor:
        mc.setBlock(old_cursor, block.AIR)
        cursor.y = mc.getHeight(cursor.x, cursor.z)

    mc.setBlock(cursor, block.STONE)

    time.sleep(0.01)
