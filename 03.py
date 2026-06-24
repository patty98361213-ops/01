# -*- coding: utf-8 -*-
import streamlit as st

# 網頁基本設定（寬版佈局，適合雙欄展示）
st.set_page_config(page_title="精品美妝 & 包款複合式優惠計算器", page_icon="🛍️", layout="wide")

from itertools import combinations
from functools import lru_cache
from collections import Counter

# -----------------------------
# 商品資料庫 (含單價與分類)
# -----------------------------
PRICES = {
    "潔顏露": 480, "紅蔘水": 580, "富勒希": 1080, "滲透精華": 1080, 
    "保濕修復霜": 1080, "體香噴霧": 680, "隔離": 780,
    "法棍包": 2680, "小方包": 2680, "巧克包": 2180, "泡芙包(小)": 1290, 
    "泡芙包(小藍)": 1390, "泡芙包(大)": 1490, "泡芙包(大藍)": 1590, 
    "泡芙肩背包": 1880, "束口後背包": 1880, "經典後背包": 1280, 
    "中夾": 1780, "短夾": 1680, "零錢夾": 1580, "長夾": 2280, "掀蓋零錢夾": 1880
}

COSMETIC_ITEMS = ["潔顏露", "紅蔘水", "富勒希", "滲透精華", "保濕修復霜", "體香噴霧", "隔離"]
BAG_ITEMS = [p for p in PRICES if p not in COSMETIC_ITEMS]

BIG_SETS = {
    ("隔離", "潔顏露", "紅蔘水", "富勒希", "保濕修復霜"): 3560,
    ("隔離", "潔顏露", "紅蔘水", "富勒希"): 2599,
    ("潔顏露", "紅蔘水", "滲透精華", "保濕修復霜"): 2880,
}

COMBOS = {
    ("潔顏露", "潔顏露"): (960, 880),
    ("潔顏露", "潔顏露", "潔顏露", "潔顏露"): (1920, 1680),
    ("紅蔘水", "紅蔘水"): (1160, 1080),
    ("紅蔘水", "紅蔘水", "紅蔘水", "紅蔘水"): (2320, 2080),
    ("隔離", "隔離", "隔離", "隔離"): (3120, 2780),
    ("富勒希", "富勒希"): (2160, 1880),
    ("富勒希", "紅蔘水"): (1660, 1480),
    ("富勒希", "潔顏露"): (1560, 1380),
    ("紅蔘水", "潔顏露"): (1060, 1000),
    ("富勒希", "保濕修復霜"): (2160, 1980),
    ("紅蔘水", "保濕修復霜"): (1660, 1480),
}

COMBOS_SORTED = sorted(COMBOS.items(), key=lambda x: (x[1][0] - x[1][1]) / x[1][0], reverse=True)

PACKAGE_TWO_ITEM_DISCOUNTS = [
    (["小方包"], ["短夾", "零錢夾"], 0.9),
    (["長夾", "掀蓋零錢夾", "中夾", "短夾", "零錢夾"], ["法棍包"], 0.95),
    (["束口後背包", "經典後背包"], None, 0.95),  
    (["束口後背包"], ["潔顏露"], 0.9),
    (["經典後背包"], ["潔顏露"], 1680),           
    (["中夾", "短夾", "零錢夾"], None, 0.95),       
    (["中夾", "短夾", "零錢夾"], ["潔顏露", "體香噴霧", "隔離"], 0.9),
    (["長夾", "掀蓋零錢夾"], None, 0.95),           
    (["長夾", "掀蓋零錢夾"], ["潔顏露", "體香噴霧", "隔離"], 0.95),      
    (["巧克包"], None, 0.95),                       
    (["泡芙包(小)", "泡芙包(小藍)", "泡芙包(大)", "泡芙包(大藍)"], None, 0.95), 
    (["泡芙包(小)", "泡芙包(小藍)", "泡芙包(大)", "泡芙包(大藍)"], ["潔顏露"], 0.9), 
    (["中夾", "短夾", "零錢夾"], ["巧克包", "泡芙包(小)", "泡芙包(小藍)", "泡芙包(大)", "泡芙包(大藍)"], 0.95) 
]

# -----------------------------
# 核心計算邏輯
# -----------------------------
def calc_original(cart):
    return sum(PRICES[p] * qty for p, qty in cart.items())

@lru_cache(maxsize=None)
def apply_combos(cart_tuple):
    cart = {item.split(":")[0]: int(item.split(":")[1]) for item in cart_tuple if int(item.split(":")[1]) > 0}
    best_price = sum(PRICES[p] * q for p, q in cart.items())
    best_plan = [("原價購買", best_price)] if best_price > 0 else []
    
    for s, price in BIG_SETS.items():
        set_counts = Counter(s)
        if all(cart.get(k, 0) >= v for k, v in set_counts.items()):
            temp = cart.copy()
            for i in s: temp[i] -= 1
            new_price, plan = apply_combos(tuple(f"{k}:{v}" for k, v in temp.items()))
            total = price + new_price
            if total < best_price:
                best_price = total
                best_plan = [(f"{'+'.join(s)} 大套組", price)] + plan
                
    for c, (_, disc) in COMBOS_SORTED:
        combo_counts = Counter(c)
        if all(
