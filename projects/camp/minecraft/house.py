from rstem.button import Button
from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
import time

house = [
    [
        '111111',
        '111111',
        '111111',
        '111111',
        '111111',
        '111111',
    ],
    [
        '111111',
        '100001',
        '100001',
        '100001',
        '100001',
        '111111',
    ],
    [
        '111111',
        '100001',
        '100001',
        '100001',
        '100001',
        '111111',
    ],
    [
        '111111',
        '100001',
        '100001',
        '100001',
        '100001',
        '111111',
    ],
    [
        '111111',
        '100001',
        '100001',
        '100001',
        '100001',
        '111111',
    ],
]

block_types = [
    block.AIR, 
    block.STONE,
    ]

def create_house(mc, house_slices, offset, base=block.STONE):
    center = mc.player.getTilePos()
    corner = center - offset
    for delta_y, house_slice in enumerate(house_slices):
        for delta_x, row in enumerate(house_slice):
            for delta_z, block_index in enumerate(row):
                block_type = block_types[int(block_index)]
                mc.setBlock(corner + Vec3(delta_x, delta_y, delta_z), block_type)
                
control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()
button = Button(7)

while True:
    if button.presses():
        create_house(mc, house, Vec3(3,1,3))

    time.sleep(0.01)

