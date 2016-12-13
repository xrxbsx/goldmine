"""Experience, ranking, and leveling related utility functions."""
from util.const import lvl_base
def get_level_xp(n):
    """Calculate the XP required to be a level."""
    return lvl_base * (n**2 + n)/2 + lvl_base

def xp_level(ixp):
    """Calculate current level from XP."""
    xp = int(ixp)
    level = 0
    while xp >= get_level_xp(level):
        xp -= get_level_xp(level)
        level += 1
    return (level, xp)
