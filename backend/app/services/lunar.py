"""农历、二十四节气、传统节日（算法计算）。"""

from __future__ import annotations

from lunar_python import Solar

# 仅展示白名单内的传统节日（格子保持简洁）
FESTIVAL_SHORT: dict[str, str] = {
    "春节": "春节",
    "元宵节": "元宵",
    "龙抬头": "龙抬头",
    "端午节": "端午",
    "七夕节": "七夕",
    "中元节": "中元",
    "中秋节": "中秋",
    "重阳节": "重阳",
    "腊八节": "腊八",
    "除夕": "除夕",
    "北方小年": "小年",
    "南方小年": "小年",
}


def get_lunar_year_month(year: int, month: int, day: int) -> str:
    """返回如「丙午年六月」的农历年月文案。"""
    solar = Solar.fromYmd(year, month, day)
    lunar = solar.getLunar()
    return f"{lunar.getYearInGanZhi()}年{lunar.getMonthInChinese()}月"


def get_day_info(year: int, month: int, day: int) -> dict[str, str | None]:
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

    festival: str | None = None
    for name in lunar.getFestivals() + lunar.getOtherFestivals():
        if name in FESTIVAL_SHORT:
            festival = FESTIVAL_SHORT[name]
            break

    return {
        "lunarText": lunar_text,
        "lunarYearMonth": f"{lunar.getYearInGanZhi()}年{month_cn}月",
        "festival": festival,
        "solarTerm": solar_term,
    }
