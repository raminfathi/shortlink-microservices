from pydantic import BaseModel, HttpUrl, Field

# --- مدل‌های مربوط به لینک ---

# ورودی کاربر برای ساخت لینک
class LinkCreateRequest(BaseModel):
    long_url: HttpUrl

# پاسخی که هنگام ساخت لینک می‌دهیم
class LinkCreateResponse(BaseModel):
    short_link: HttpUrl
    long_url: HttpUrl

# VVV --- این مدل جدید است --- VVV
# مدل پاسخ برای آمار لینک (شامل QR Code)
# این کلاس از LinkCreateResponse ارث‌بری می‌کند، یعنی فیلدهای قبلی را دارد
# و فیلد جدید qr_code_url به آن اضافه می‌شود.
class LinkStats(LinkCreateResponse):
    # ما از Field(default=None) استفاده می‌کنیم تا این فیلد اختیاری باشد
    # (چون ممکن است worker هنوز آن را نساخته باشد)
    qr_code_url: str | None = Field(default=None)
# ^^^ --- پایان مدل جدید --- ^^^