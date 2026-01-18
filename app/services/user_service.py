import asyncio
from uuid import UUID

from app.core.supabase_client import supabase


async def update_role(user_id: UUID, new_role: str):
    """Update the role for a supabase user using the admin API.

    Runs sync supabase client calls in a separate thread so callers can
    await this function without blocking the event loop.
    """

    def _sync_update():
        return supabase.auth.admin.update_user_by_id(
            str(user_id), {"data": {"role": new_role}}
        )

    return await asyncio.to_thread(_sync_update)
