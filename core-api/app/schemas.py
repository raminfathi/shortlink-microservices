from pydantic import BaseModel, HttpUrl, Field

# --- Link Models ---

# User input for creating a link
class LinkCreateRequest(BaseModel):
    long_url: HttpUrl

# Response when a link is created
class LinkCreateResponse(BaseModel):
    short_link: HttpUrl
    long_url: HttpUrl

# Response for link stats (including QR Code)
class LinkStats(LinkCreateResponse):
    # Optional field, as worker might not have generated it yet
    qr_code_url: str | None = Field(default=None)
    unique_clicks: int = 0

# VVV --- Phase 8: New Schema for History --- VVV
class ClickHistoryItem(BaseModel):
    timestamp: int
    count: int
# ^^^ --- End of new schema --- ^^^