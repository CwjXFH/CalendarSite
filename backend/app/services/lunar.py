"""农历、二十四节气、传统节日（算法计算）。"""

from __future__ import annotations

from lunar_python import Lunar, Solar

# 键是农历月日，不是公历。春节、中秋等按农历固定，对应公历每年不同。
# 调用方先 Solar.fromYmd → getLunar()，再用当天的月、日查表。
# 闰月 month 为负，不会命中正数键（闰二月初二不算龙抬头）。
# 除夕不进表：腊月有时廿九、有时三十，由 _festival 判断下一天是否换年。
FESTIVAL_BY_LUNAR_MD: dict[tuple[int, int], str] = {
    (1, 1): "春节",
    (1, 15): "元宵",
    (2, 2): "龙抬头",
    (5, 5): "端午",
    (7, 7): "七夕",
    (7, 15): "中元",
    (8, 15): "中秋",
    (9, 9): "重阳",
    (12, 8): "腊八",
    (12, 23): "小年",
    (12, 24): "小年",
}


def _festival(lunar: Lunar) -> str | None:
    month = lunar.getMonth()
    day = lunar.getDay()
    name = FESTIVAL_BY_LUNAR_MD.get((month, day))
    if name is not None:
        return name
    if abs(month) == 12 and day >= 29:
        if lunar.next(1).getYear() != lunar.getYear():
            return "除夕"
    return None


def _cn_list(values: object) -> list[str]:
    if values is None:
        return []
    return [str(item) for item in values if str(item).strip() != ""]


def get_day_info(year: int, month: int, day: int) -> dict:
    solar = Solar.fromYmd(year, month, day)
    lunar = solar.getLunar()

    day_cn = lunar.getDayInChinese()
    month_cn = lunar.getMonthInChinese()

    if day_cn == "初一":
        lunar_text = f"{month_cn}月"
    else:
        lunar_text = day_cn

    jie_qi = lunar.getJieQi()
    solar_term = jie_qi if jie_qi else None
    week_cn = solar.getWeekInChinese()
    weekday = week_cn if week_cn.startswith("星期") else f"星期{week_cn}"

    return {
        "lunarText": lunar_text,
        "lunarYearMonth": f"{lunar.getYearInGanZhi()}年{month_cn}月",
        "lunarMonthDay": f"{month_cn}月{day_cn}",
        "ganZhi": (
            f"{lunar.getYearInGanZhi()}年 {lunar.getMonthInGanZhi()}月 "
            f"{lunar.getDayInGanZhi()}日"
        ),
        "weekday": weekday,
        "festival": _festival(lunar),
        "solarTerm": solar_term,
        "yi": _cn_list(lunar.getDayYi()),
        "ji": _cn_list(lunar.getDayJi()),
    }
