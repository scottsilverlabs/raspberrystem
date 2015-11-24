import sys
from struct import unpack

block_map = {
    0: 'AIR',
    1: 'STONE',
    2: 'GRASS',
    3: 'DIRT',
    4: 'COBBLESTONE',
    5: 'WOOD_PLANKS',
    6: 'SAPLING',
    7: 'BEDROCK',
    8: 'WATER_FLOWING',
    9: 'WATER_STATIONARY',
    10: 'LAVA_FLOWING',
    11: 'LAVA_STATIONARY',
    12: 'SAND',
    13: 'GRAVEL',
    14: 'GOLD_ORE',
    15: 'IRON_ORE',
    16: 'COAL_ORE',
    17: 'WOOD',
    18: 'LEAVES',
    20: 'GLASS',
    21: 'LAPIS_LAZULI_ORE',
    22: 'LAPIS_LAZULI_BLOCK',
    24: 'SANDSTONE',
    26: 'BED',
    30: 'COBWEB',
    31: 'GRASS_TALL',
    35: 'WOOL',
    37: 'FLOWER_YELLOW',
    38: 'FLOWER_CYAN',
    39: 'MUSHROOM_BROWN',
    40: 'MUSHROOM_RED',
    41: 'GOLD_BLOCK',
    42: 'IRON_BLOCK',
    43: 'STONE_SLAB_DOUBLE',
    44: 'STONE_SLAB',
    45: 'BRICK_BLOCK',
    46: 'TNT',
    47: 'BOOKSHELF',
    48: 'MOSS_STONE',
    49: 'OBSIDIAN',
    50: 'TORCH',
    51: 'FIRE',
    53: 'STAIRS_WOOD',
    54: 'CHEST',
    56: 'DIAMOND_ORE',
    57: 'DIAMOND_BLOCK',
    58: 'CRAFTING_TABLE',
    59: 'SEEDS',
    60: 'FARMLAND',
    61: 'FURNACE_INACTIVE',
    62: 'FURNACE_ACTIVE',
    64: 'DOOR_WOOD',
    65: 'LADDER',
    67: 'STAIRS_COBBLESTONE',
    68: 'WALL_SIGN',
    71: 'DOOR_IRON',
    73: 'REDSTONE_ORE',
    74: 'LIT_REDSTONE_ORE',
    78: 'SNOW',
    79: 'ICE',
    80: 'SNOW_BLOCK',
    81: 'CACTUS',
    82: 'CLAY',
    83: 'SUGAR_CANE',
    85: 'FENCE',
    87: 'NETHERRACK',
    89: 'GLOWSTONE_BLOCK',
    95: 'BEDROCK_INVISIBLE',
    96: 'TRAPDOOR',
    98: 'STONE_BRICK',
    102: 'GLASS_PANE',
    103: 'MELON',
    107: 'FENCE_GATE',
    108: 'BRICK_STAIRS',
    109: 'STONE_BRICK_STAIRS',
    112: 'NETHER_BRICK',
    114: 'NETHER_BRICK_STAIRS',
    128: 'SANDSTONE_STAIRS',
    155: 'QUARTZ_BLOCK',
    156: 'QUARTZ_STAIRS',
    245: 'STONE_CUTTER',
    246: 'GLOWING_OBSIDIAN',
    247: 'NETHER_REACTOR_CORE',
    248: 'UPDATE_GAME_BLOCK_1',
    249: 'UPDATE_GAME_BLOCK_2',
}


with open(sys.argv[1], 'rb') as f:
    filebytes = f.read()

def offsetof(s, data):
    return data.index(s.encode()) + len(s)
    
def index2char(i):
    if i < 10:
        return chr(ord('0') + i)
    i -= 10
    if i < 26:
        return chr(ord('A') + i)
    i -= 26
    return chr(ord('a') + i)
        
field_names = ['Height', 'Length', 'Width', 'Data', 'Blocks']
fields = {}
for field_name in field_names:
    fields[field_name] = offsetof(field_name, filebytes)

data_len = unpack(">I", filebytes[fields['Data']:][:4])[0]
data = filebytes[fields['Data']+4:][:data_len]
blks_len = unpack(">I", filebytes[fields['Blocks']:][:4])[0]
blks = filebytes[fields['Blocks']+4:][:blks_len]
assert(data_len == blks_len)

height = unpack(">H", filebytes[fields['Height']:][:2])[0]
length = unpack(">H", filebytes[fields['Length']:][:2])[0]
width = unpack(">H", filebytes[fields['Width']:][:2])[0]

block_types = [(0,0)]
print('house = [')
for h in range(height):
    print('    [')
    for l in range(length):
        print('        "', end='')
        for w in range(width):
            offset = h*length*width + l*width + w
            block_type = (blks[offset], data[offset])
            if not block_type in block_types:
                block_types += [block_type]
            print(index2char(block_types.index(block_type)), end='')
        print('",')
    print('    ],')
print(']')

print('block_types = [')
for blk, data in block_types:
    if data == 0 and blk in block_map:
        block_str = '    block.{},'.format(block_map[blk])
    else:
        if blk in block_map:
            block_str = '    block.Block({}, {}), # {}'.format(blk, data, block_map[blk])
        else:
            block_str = '    block.Block({}, {}),'.format(blk, data)
    c = index2char(block_types.index((blk, data)))
    print('{:50}# {}'.format(block_str, c))
print('    ]')

