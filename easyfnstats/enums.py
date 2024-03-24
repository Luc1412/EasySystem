from enum import Enum


class PromoDenyReason(Enum):
    WRONG_INVITE_COUNT = 0
    INVALID_INVITE = 1
    GUILD_MISSING_BOT = 2
