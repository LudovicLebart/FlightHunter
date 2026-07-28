from __future__ import annotations

import datetime
from dataclasses import dataclass, asdict


@dataclass
class Offer:
    provider: str
    destination_code: str
    destination_name: str
    departure_date: datetime.date
    return_date: datetime.date
    nights: int
    price_total_cad: float
    hotel_name: str
    board_type: str
    sargassum_risk: str
    url: str
    scraped_at: datetime.datetime

    @property
    def price_per_person(self) -> float:
        from config import PAX
        return self.price_total_cad / PAX if PAX else self.price_total_cad

    def to_dict(self) -> dict:
        d = asdict(self)
        d["departure_date"] = self.departure_date.isoformat()
        d["return_date"] = self.return_date.isoformat()
        d["scraped_at"] = self.scraped_at.isoformat()
        d["price_per_person"] = round(self.price_per_person, 2)
        return d
