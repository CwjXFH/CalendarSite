"""二十四节气（公历年 + 交节时刻）。不包含黄历宜忌。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from lunar_python import Solar

from app.services.lunar import get_day_info

JIEQI_24 = (
    "小寒",
    "大寒",
    "立春",
    "雨水",
    "惊蛰",
    "春分",
    "清明",
    "谷雨",
    "立夏",
    "小满",
    "芒种",
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "处暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
    "冬至",
)

JIEQI_SLUG: dict[str, str] = {
    "小寒": "xiaohan",
    "大寒": "dahan",
    "立春": "lichun",
    "雨水": "yushui",
    "惊蛰": "jingzhe",
    "春分": "chunfen",
    "清明": "qingming",
    "谷雨": "guyu",
    "立夏": "lixia",
    "小满": "xiaoman",
    "芒种": "mangzhong",
    "夏至": "xiazhi",
    "小暑": "xiaoshu",
    "大暑": "dashu",
    "立秋": "liqiu",
    "处暑": "chushu",
    "白露": "bailu",
    "秋分": "qiufen",
    "寒露": "hanlu",
    "霜降": "shuangjiang",
    "立冬": "lidong",
    "小雪": "xiaoxue",
    "大雪": "daxue",
    "冬至": "dongzhi",
}

SLUG_TO_JIEQI = {slug: name for name, slug in JIEQI_SLUG.items()}

JIEQI_BLURB: dict[str, str] = {
    "小寒": "小寒是冬季倒数第二个节气，表示寒冷开始加深。",
    "大寒": "大寒是二十四节气的最后一个，通常是一年中最冷的时段。",
    "立春": "立春是二十四节气之首，标志着春季开始。",
    "雨水": "雨水节气降水增多，气温回升，冰雪融化。",
    "惊蛰": "惊蛰时春雷始鸣，气温回暖，蛰虫出土。",
    "春分": "春分昼夜几乎等长，此后北半球白昼渐长。",
    "清明": "清明既是节气也是传统节日，气候清澈明朗，常见降雨。",
    "谷雨": "谷雨取「雨生百谷」之意，降水明显增加，利于播种。",
    "立夏": "立夏标志着夏季开始，气温明显升高。",
    "小满": "小满指夏熟作物籽粒开始饱满，但尚未成熟。",
    "芒种": "芒种是播种有芒作物的时节，农事繁忙。",
    "夏至": "夏至是北半球白昼最长的一天，此后白昼渐短。",
    "小暑": "小暑表示盛夏将至，气温升高但还未到最热。",
    "大暑": "大暑通常是一年中最热的节气，多高温和雷雨。",
    "立秋": "立秋标志着秋季开始，此后暑热逐渐减退。",
    "处暑": "处暑表示炎热结束，「处」即终止。",
    "白露": "白露时昼夜温差加大，清晨可见露水。",
    "秋分": "秋分昼夜几乎等长，此后北半球白昼渐短。",
    "寒露": "寒露表示露水更凉，天气由凉转寒。",
    "霜降": "霜降是秋季最后一个节气，表示天气渐冷、初霜出现。",
    "立冬": "立冬标志着冬季开始，万物收藏。",
    "小雪": "小雪表示降雪开始，但雪量通常不大。",
    "大雪": "大雪时降雪概率增大，天气更冷。",
    "冬至": "冬至是北半球白昼最短的一天，此后白昼渐长。",
}


@dataclass(frozen=True)
class JieqiItem:
    name: str
    slug: str
    when: date
    hour: int
    minute: int
    second: int
    weekday: str
    lunar_text: str
    lunar_year_month: str

    @property
    def time_text(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"

    @property
    def datetime_text(self) -> str:
        return (
            f"{self.when.year}年{self.when.month}月{self.when.day}日"
            f"{self.weekday} {self.time_text}"
        )


def _table(year: int, month: int, day: int) -> dict:
    return Solar.fromYmd(year, month, day).getLunar().getJieQiTable()


@lru_cache(maxsize=128)
def get_jieqi_year(year: int) -> tuple[JieqiItem, ...]:
    # 冬至落在表的「下一年」窗口，需拼 1 月、年中、次年 1 月。
    found: dict[str, object] = {}
    for y, month, day in (
        (year, 1, 1),
        (year, 6, 15),
        (year, 12, 31),
        (year + 1, 1, 15),
    ):
        table = _table(y, month, day)
        for name in JIEQI_24:
            solar = table.get(name)
            if solar is None or solar.getYear() != year:
                continue
            found[name] = solar

    items: list[JieqiItem] = []
    for name in JIEQI_24:
        solar = found.get(name)
        if solar is None:
            continue
        info = get_day_info(solar.getYear(), solar.getMonth(), solar.getDay())
        week_cn = solar.getWeekInChinese()
        weekday = week_cn if week_cn.startswith("星期") else f"星期{week_cn}"
        items.append(
            JieqiItem(
                name=name,
                slug=JIEQI_SLUG[name],
                when=date(solar.getYear(), solar.getMonth(), solar.getDay()),
                hour=solar.getHour(),
                minute=solar.getMinute(),
                second=solar.getSecond(),
                weekday=weekday,
                lunar_text=str(info["lunarText"]),
                lunar_year_month=str(info["lunarYearMonth"]),
            )
        )
    return tuple(items)


def get_jieqi_by_slug(year: int, slug: str) -> JieqiItem | None:
    name = SLUG_TO_JIEQI.get(slug)
    if name is None:
        return None
    return next((item for item in get_jieqi_year(year) if item.name == name), None)


def jieqi_around(year: int) -> tuple[JieqiItem, ...]:
    items = [*get_jieqi_year(year - 1), *get_jieqi_year(year), *get_jieqi_year(year + 1)]
    return tuple(sorted(items, key=lambda item: (item.when, item.hour, item.minute)))


def nearest_jieqi(day: date, items: tuple[JieqiItem, ...] | None = None) -> tuple[JieqiItem, bool] | None:
    pool = items if items is not None else jieqi_around(day.year)
    if pool == ():
        return None

    def closer(item: JieqiItem) -> tuple[int, int]:
        delta = abs((item.when - day).days)
        upcoming_first = 0 if item.when >= day else 1
        return (delta, upcoming_first)

    item = min(pool, key=closer)
    return item, item.when < day
