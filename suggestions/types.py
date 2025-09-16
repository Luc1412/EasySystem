from typing import TypedDict


class SuggestionsGuildSettings(TypedDict):
    channel_id: int | None
    upvote_emoji: str
    downvote_emoji: str
