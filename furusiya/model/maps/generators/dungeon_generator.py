import math
from random import randint
import random

from attrdict import AttrDict

import colors
from constants import GROUND_CHARACTER, WALL_CHARACTER, color_light_ground, color_dark_ground, color_dark_wall, color_light_wall
from main_interface import Game
from model.config import config
from model.components.walkers.random_walker import RandomWalker
from model.item_callbacks import cast_heal, cast_lightning, cast_fireball, cast_confuse
from model.rect import Rect
from model.factories import monster_factory, item_factory


class DungeonGenerator:
    """
    Generates a multi-room dungeon map in entirety, by mutating map tiles.
    Includes population of monsters, map items, etc.
    """
    NUM_ITEMS = (10, 20)
    NUM_MONSTERS = (30, 40)

    NUM_ROOMS = (15, 30)
    ROOM_MAX_SIZE = 10
    ROOM_MIN_SIZE = 6
    NUM_TREES = 1800
    MAX_ROOM_MONSTERS = 3
    MAX_ROOM_ITEMS = 2

    def __init__(self, width, height, area_map):
        self._width = width
        self._height = height
        self._area_map = area_map
        self._generate_rooms()
        self._generate_objects()

    def _generate_rooms(self):
        # TODO: dry this block with forest generator
        for x in range(0, self._area_map.width):
            for y in range(0, self._area_map.height):
                self._convert_to_wall(self._area_map.tiles[x][y])

        rooms = []
        rooms_to_generate = random.randint(DungeonGenerator.NUM_ROOMS[0], DungeonGenerator.NUM_ROOMS[1])

        while rooms_to_generate:
            # random width and height
            w = randint(DungeonGenerator.ROOM_MIN_SIZE, DungeonGenerator.ROOM_MAX_SIZE)
            h = randint(DungeonGenerator.ROOM_MIN_SIZE, DungeonGenerator.ROOM_MAX_SIZE)
            # random position without going out of the boundaries of the map
            x = randint(0, self._area_map.width - w - 1)
            y = randint(0, self._area_map.height - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # run through the other rooms and see if they intersect with this one
            failed = False
            for other_room in rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break

            if not failed:
                # this means there are no intersections, so this room is valid

                # "paint" it to the map's tiles
                self._create_room(new_room)
                rooms_to_generate -= 1

                # center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                if len(rooms) == 0:
                    # this is the first room, where the player starts at
                    Game.player.x = new_x
                    Game.player.y = new_y

                else:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel

                    # center coordinates of previous room
                    (prev_x, prev_y) = rooms[len(rooms) - 1].center()

                    # draw a coin (random number that is either 0 or 1)
                    if randint(0, 1):
                        # first move horizontally, then vertically
                        self._create_h_tunnel(prev_x, new_x, prev_y)
                        self._create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        self._create_v_tunnel(prev_y, new_y, prev_x)
                        self._create_h_tunnel(prev_x, new_x, new_y)

                # finally, append the new room to the list
                rooms.append(new_room)

    def _create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self._convert_to_ground(self._area_map.tiles[x][y])

    def _create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self._convert_to_ground(self._area_map.tiles[x][y])


    def _create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self._convert_to_ground(self._area_map.tiles[x][y])

    # TODO: DRY with forest generator
    def _convert_to_ground(self, map_tile):
        map_tile.is_walkable = True
        map_tile.block_sight = False
        map_tile.character = GROUND_CHARACTER
        map_tile.colour = color_light_ground
        map_tile.dark_colour = color_dark_ground

    # TODO: DRY with forest generator
    def _convert_to_wall(self, map_tile):
        map_tile.is_walkable = False
        map_tile.block_sight = True
        map_tile.character = WALL_CHARACTER
        map_tile.colour = color_light_wall
        map_tile.dark_colour = color_dark_wall

    # TODO: DRY with forest generator
    def _generate_objects(self):
        self._generate_monsters()
        self._generate_items()

    # TODO: DRY with forest generator
    def _find_empty_tile(self):
        while True:
            x = randint(0, self._area_map.width - 1)
            y = randint(0, self._area_map.height - 1)
            if self._area_map.tiles[x][y].is_walkable:
                break
        return x, y

    def _generate_monsters(self):
        # choose random number of monsters
        num_monsters = randint(DungeonGenerator.NUM_MONSTERS[0], DungeonGenerator.NUM_MONSTERS[1])

        for i in range(num_monsters):
            # choose random spot for this monster
            x = randint(0, self._area_map.width)
            y = randint(0, self._area_map.width)

            # only place it if the tile is not blocked
            # TODO: DRY with forest generator
            if self._area_map.is_walkable(x, y):
                choice = randint(0, 100)
                if choice <= 55: 
                    name = 'bushslime'
                    data = config.data.enemies.bushslime
                    colour = colors.desaturated_green
                elif choice <= 55 + 30:
                    name = 'steelhawk'
                    data = config.data.enemies.steelhawk
                    colour = colors.light_blue
                else:  # 15
                    name = 'tigerslash'
                    data = config.data.enemies.tigerslash
                    colour = colors.orange

                monster = monster_factory.create_monster(data, x, y, colour, name)
                self._area_map.entities.append(monster)

    def _generate_items(self):
        # choose random number of items
        num_items = randint(DungeonGenerator.NUM_ITEMS[0], DungeonGenerator.NUM_ITEMS[1])

        for i in range(num_items):
            # choose random spot for this item
            x = randint(0, self._area_map.width)
            y = randint(0, self._area_map.width)

            # only place it if the tile is not blocked
            # TODO: DRY with forest generator            
            if self._area_map.is_walkable(x, y):
                dice = randint(0, 100)
                if dice < 70:
                    # create a healing potion (70% chance)
                    char = '!'
                    name = 'healing potion'
                    color = colors.violet
                    use_func = cast_heal

                elif dice < 70 + 10:
                    # create a lightning bolt scroll (15% chance)
                    char = '#'
                    name = 'scroll of lightning bolt'
                    color = colors.light_yellow
                    use_func = cast_lightning

                elif dice < 70 + 10 + 10:
                    # create a fireball scroll (10% chance)
                    char = '#'
                    name = 'scroll of fireball'
                    color = colors.light_yellow
                    use_func = cast_fireball

                else: # 10
                    # create a confuse scroll (15% chance)
                    char = '#'
                    name = 'scroll of confusion'
                    color = colors.light_yellow
                    use_func = cast_confuse

                item = item_factory.create_item(x, y, char, name, color, use_func)

                self._area_map.entities.append(item)
                item.send_to_back()  # items appear below other objects
