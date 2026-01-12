from datetime import datetime
from zoneinfo import ZoneInfo

def time_zone(location: str = "Asia/Seoul") -> datetime:
    """
    서머 타임 자동 반영.
    
    상세 지역 확인:
        - print(zoneinfo.available_timezones())
        - ⚠️ 너무 많음.

    앞(Region):
        - Asia, Europe, America, Africa, Pacific, Indian, Atlantic,
        Antarctica, Arctic, Etc

    뒤(Location):
        - Seoul, Tokyo, New_York, London
    """

    return datetime.now(ZoneInfo(location))