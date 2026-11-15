import asyncio
import time
from lib.odoo.read import odoo_read

CACHE_TTL = 300 

# guild id -> (time fetched, {role id: role name})
_role_cache: dict[str, tuple[float, dict[str, str]]] = {}

async def get_self_assignable_roles(guild_id) -> dict[str, str]:
    key = str(guild_id)
    hit = _role_cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL:
        return hit[1]

    try:
        records = await asyncio.to_thread(
            odoo_read,
            "discord.role",
            [
                ["server.guild_id", "=", key],
                ["user_selectable", "=", True],
                ["discord_id", "!=", False],
            ],
            ["name", "discord_id"],
        )
    except Exception as ex:
        print(f"Error fetching roles from Odoo: {ex!r}")
        if hit:
            # Odoo is unreachable: a stale list is better than none
            return hit[1]
        raise

    roles = {str(record["discord_id"]): record["name"] for record in records}
    _role_cache[key] = (time.monotonic(), roles)
    return roles

def invalidate_roles(guild_id=None):
    """Drop the cached role list for one guild, or for all guilds."""
    if guild_id is None:
        _role_cache.clear()
    else:
        _role_cache.pop(str(guild_id), None)