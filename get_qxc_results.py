# -*- coding: utf-8 -*-
"""
获取七星彩近100期开奖结果
数据来源: https://datachart.500.com/qxc/history/inc/history.php?limit=100&type=0
"""
import re
import csv
import requests

URL = "https://datachart.500.com/qxc/history/inc/history.php?limit=200&type=0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    # 页面为 GB2312 编码
    return r.content.decode("gb2312", errors="replace")


def parse_results(html: str):
    """
    解析每行 tr:
      <td>期号</td><td class="cfont2">中奖号码 1 2 3 4 5 6 7<span ...></span></td>
      <td>仹选和值</td><td>全国销量</td><td>开奖日期</td>
    """
    row_pattern = re.compile(
        r'<td class="t_tr1">(\d{5})</td>\s*'                    # 期号
        r'<td class="cfont2">([\d\s]+?)<span',                 # 中奖号码
        re.DOTALL,
    )
    extra_pattern = re.compile(
        r'<td class="cfont2">[\d\s]+?<span class="cBlue"> </span></td>\s*'
        r'<td>(\d+)</td>\s*'                                    # 仹选和值
        r'<td class="t_tr1">(\d+)</td>\s*'                      # 全国销量
        r'<td class="t_tr1">(\d{4}-\d{2}-\d{2})</td>',         # 开奖日期
    )
    rows = []
    # 一次性提取所有信息
    for match in row_pattern.finditer(html):
        issue = match.group(1)
        numbers = " ".join(match.group(2).split())
        # 在 match 末尾之后寻找 仹选和值/销量/日期
        tail = html[match.end(): match.end() + 400]
        m_extra = re.search(
            r'<td>(\d+)</td>\s*<td class="t_tr1">(\d+)</td>\s*<td class="t_tr1">(\d{4}-\d{2}-\d{2})</td>',
            tail,
        )
        if m_extra:
            sum_value, sales, draw_date = m_extra.groups()
            rows.append({
                "期号": issue,
                "中奖号码": numbers,
                "仹选和值": sum_value,
                "全国销量(元)": sales,
                "开奖日期": draw_date,
            })
    return rows


def save_csv(rows, path: str):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    html = fetch_html(URL)
    rows = parse_results(html)
    print(f"共获取 {len(rows)} 期开奖结果\n")
    # 控制台以表格打印
    print(f"{'期号':<8}{'日期':<14}{'中奖号码':<22}{'仹选和值':<10}{'全国销量(元)'}")
    print("-" * 80)
    for r in rows:
        print(
            f"{r['期号']:<8}{r['开奖日期']:<14}{r['中奖号码']:<22}"
            f"{r['仹选和值']:<10}{r['全国销量(元)']}"
        )
    # 保存 CSV
    save_csv(rows, "qxc_last100.csv")
    print(f"\n已保存到: qxc_last100.csv")


if __name__ == "__main__":
    main()
