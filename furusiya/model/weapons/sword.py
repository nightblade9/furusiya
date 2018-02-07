from random import randint

import colors
import config
from main_interface import message
from model.components.ai.base import AI
from model.components.ai.monster import StunnedMonster


class Sword:
    """
    A sword. It sometimes incapacitates (stuns) the opponent due to damage
    inflicted. As a class, it doesn't calculate or deal damage; merely adds
    effects on top of the combat algorithms. (This is true of all weapons.)
    """
    def __init__(self, owner):
        self.owner = owner

    def attack(self, target):
        if config.data.features.swordStuns:
            if randint(0, 100) <= config.data.weapons.swordStunProbability:
                target_ai = target.get_component(AI)
                if config.data.features.stunsStack:
                    if isinstance(target_ai, StunnedMonster):
                        # Stack the stun
                        target_ai.num_turns += config.data.weapons.numTurnsStunned
                    else:
                        target.set_component(StunnedMonster(target))
                else:
                    # Copy-pasta from two lines above
                    target.set_component(StunnedMonster(target))
                message('{} looks incapacitated!'.format(target.name), colors.light_green)