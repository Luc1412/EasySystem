from __future__ import annotations

from typing import TypedDict


class BanTrapGuildSettings(TypedDict):
    channel_id: int | None
    log_channel_id: int | None
