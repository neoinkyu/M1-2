from datetime import date

from pydantic import BaseModel, Field


class DataCreate(BaseModel):
    date: date
    value: float = Field(..., description="대표 시계열 값(PV)")
    memo: str | None = None

    posts: int | None = None
    pages: int | None = None
    users: int | None = None
    pv: int | None = None
    adsense_estimated: float | None = None

    gsc_type: str | None = None
    gsc_clicks: int | None = None
    gsc_impressions: int | None = None
    gsc_ctr: float | None = None
    gsc_position: float | None = None


class DataUpdate(BaseModel):
    value: float | None = None
    memo: str | None = None

    posts: int | None = None
    pages: int | None = None
    users: int | None = None
    pv: int | None = None
    adsense_estimated: float | None = None

    gsc_type: str | None = None
    gsc_clicks: int | None = None
    gsc_impressions: int | None = None
    gsc_ctr: float | None = None
    gsc_position: float | None = None