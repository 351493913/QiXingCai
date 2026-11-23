# -*- coding: utf-8 -*-
"""
五行推算 v3: 在 v2 (五行分布) 基础上, 增加 大小 关系细分
  对每个位置的每个数字, 统计其后一期数字的:
    - 五行分布 (金木水火土)
    - 大小分布 (前6位: 0-4小, 5-9大; 第7位: 0-7小, 8-14大)
    - 五行x大小 组合分布
  预测: 组合频次最高的类别 -> 从该类别对应数字中选候选
"""
import csv
from collections import Counter
from itertools import product

CSV_PATH = "qxc_last100.csv"
WINDOW = 80  # 训练窗口大小 (回测最优)

ELEMENT_MAP = {
    0: "土", 1: "水", 2: "火", 3: "木", 4: "金",
    5: "土", 6: "水", 7: "火", 8: "木", 9: "金",
    10: "土", 11: "水", 12: "火", 13: "木", 14: "金",
}


def size_of(n, pos):
    """大小判定: 前6位 0-4小, 5-9大; 第7位 0-7小, 8-14大"""
    if pos < 6:
        return "小" if n <= 4 else "大"
    return "小" if n <= 7 else "大"


def digits_range(pos):
    return range(10) if pos < 6 else range(15)


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({
                "期号": r["期号"],
                "日期": r["开奖日期"],
                "nums": [int(x) for x in r["中奖号码"].split()],
            })
    rows.sort(key=lambda x: x["期号"])
    return rows


def main():
    rows = load(CSV_PATH)
    pos_names = ["第1位", "第2位", "第3位", "第4位", "第5位", "第6位", "第7位(特)"]

    latest = rows[-1]
    train = rows[-(WINDOW + 1):] if len(rows) > WINDOW else rows

    print(f"数据: {len(rows)} 期 ({rows[0]['期号']} ~ {rows[-1]['期号']}), 训练窗口最近 {WINDOW} 期")
    print(f"最新一期: {latest['期号']} ({latest['日期']})")
    print(f"号码:     {' '.join(str(n) for n in latest['nums'])}")
    print(f"五行:     {' '.join(ELEMENT_MAP[n] for n in latest['nums'])}")
    print(f"大小:     {' '.join(size_of(n, i) for i, n in enumerate(latest['nums']))}\n")

    # === 一、统计: 每个位置 每个数字 -> 下一期 五行/大小/组合 分布 ===
    wuxing_stats = [[Counter() for _ in range(15)] for _ in range(7)]
    size_stats = [[Counter() for _ in range(15)] for _ in range(7)]
    combo_stats = [[Counter() for _ in range(15)] for _ in range(7)]
    digit_stats = [[Counter() for _ in range(15)] for _ in range(7)]

    for i in range(len(train) - 1):
        for pos in range(7):
            d = train[i]["nums"][pos]
            nxt = train[i + 1]["nums"][pos]
            el = ELEMENT_MAP[nxt]
            sz = size_of(nxt, pos)
            wuxing_stats[pos][d][el] += 1
            size_stats[pos][d][sz] += 1
            combo_stats[pos][d][(el, sz)] += 1
            digit_stats[pos][d][nxt] += 1

    print("=" * 95)
    print("一、各位置 每个数字 -> 下一期 五行 / 大小 / 组合 分布")
    print("=" * 95)

    for pos in range(7):
        print(f"\n【{pos_names[pos]}】 (大小: {'0-4小 5-9大' if pos < 6 else '0-7小 8-14大'})")
        for d in digits_range(pos):
            c = combo_stats[pos][d]
            if not c:
                continue
            total = sum(c.values())
            parts = []
            for (el, sz), cnt in c.most_common():
                pct = cnt / total * 100
                nums_in = [n for n in digits_range(pos)
                           if ELEMENT_MAP[n] == el and size_of(n, pos) == sz]
                parts.append(f"{el}{sz}={cnt}({pct:.0f}%)({'/'.join(str(n) for n in nums_in)})")
            print(f"  {d:>2}({ELEMENT_MAP[d]}{size_of(d, pos)}) 共{total:>3}对 -> {' '.join(parts)}")

    # === 二、下一期推算 (五行 + 大小 组合) ===
    print("\n" + "=" * 95)
    print("二、下一期推算 (基于 五行x大小 组合分布)")
    print("=" * 95)

    predictions = []
    for pos in range(7):
        cur = latest["nums"][pos]
        c = combo_stats[pos][cur]
        dc = digit_stats[pos][cur]

        print(f"\n【{pos_names[pos]}】 当前={cur}({ELEMENT_MAP[cur]}{size_of(cur, pos)})")

        if not c:
            print("  历史无该数字转换数据, 退回全局")
            continue

        total = sum(c.values())
        print(f"  组合分布 (共{total}对):")
        for (el, sz), cnt in c.most_common():
            pct = cnt / total * 100
            nums_in = [n for n in digits_range(pos)
                       if ELEMENT_MAP[n] == el and size_of(n, pos) == sz]
            print(f"    {el}+{sz}: {cnt}次({pct:.1f}%)  对应数字: {nums_in}")

        # 按组合频次排序收集 Top4 候选
        top4 = []
        for (el, sz), _ in c.most_common():
            nums_in = [n for n in digits_range(pos)
                       if ELEMENT_MAP[n] == el and size_of(n, pos) == sz]
            nums_in.sort(key=lambda n: -dc.get(n, 0))
            for n in nums_in:
                if n not in top4:
                    top4.append(n)
                    if len(top4) >= 4:
                        break
            if len(top4) >= 4:
                break

        top_combo = c.most_common(1)[0][0]
        print(f"  >>> 最可能组合: {top_combo[0]}+{top_combo[1]}  候选: {top4}")
        predictions.append(top4)

    # === 三、综合预测 ===
    print("\n" + "=" * 95)
    print("三、综合预测 (每位 Top 4 候选)")
    print("=" * 95)
    for pos in range(7):
        cur = latest["nums"][pos]
        cands = predictions[pos] if pos < len(predictions) else []
        print(f"  {pos_names[pos]}: 当前={cur}({ELEMENT_MAP[cur]}{size_of(cur, pos)})  "
              f"候选=[{' '.join(str(n) for n in cands)}]")

    main_pick = [c[0] for c in predictions]
    print(f"\n  主推(Top1): {' '.join(str(n) for n in main_pick)}")
    print(f"  五行:       {' '.join(ELEMENT_MAP[n] for n in main_pick)}")
    print(f"  大小:       {' '.join(size_of(n, i) for i, n in enumerate(main_pick))}")

    # Top2 笛卡尔积 前8
    top2 = [c[:2] for c in predictions]
    top2_freq = []
    for pos in range(7):
        cur = latest["nums"][pos]
        dc = digit_stats[pos][cur]
        f0 = dc.get(top2[pos][0], 0) if len(top2[pos]) > 0 else 0
        f1 = dc.get(top2[pos][1], 0) if len(top2[pos]) > 1 else 0
        top2_freq.append((f0, f1))

    combs = []
    for combo in product(range(2), repeat=7):
        if any(combo[i] >= len(top2[i]) for i in range(7)):
            continue
        score = sum(top2_freq[i][combo[i]] for i in range(7))
        nums = [top2[i][combo[i]] for i in range(7)]
        combs.append((score, nums))
    combs.sort(key=lambda x: -x[0])
    seen = set()
    shown = 0
    print("\n  备选组合(Top2笛卡尔积, 按频次和排序, 前8):")
    for score, nums in combs:
        key = tuple(nums)
        if key in seen:
            continue
        seen.add(key)
        print(f"    {shown+1:>2}. 频次和={score:>3}  {' '.join(str(n) for n in nums)}")
        shown += 1
        if shown >= 8:
            break


if __name__ == "__main__":
    main()
