"""Experience, ranking, and leveling related utility functions."""
def get_level_xp(n):
    """Calculate the XP required to be a level."""
    return 75*(n**2 + n)/2 + 75

def xp_level(ixp):
    """Calculate current level from XP."""
    xp = int(ixp)
    level = 0
    while xp >= get_level_xp(level):
        xp -= get_level_xp(level)
        level += 1
    return (level, xp)
