#!/usr/bin/env python3
"""校验导出的 PPTX：页数、可编辑文本、图片素材数、关键内容抽查。

用途：Ardot 导出 PPTX 后的落地校验。全元素可编辑的硬性要求是
媒体素材数为 0（图表全部为矢量+文本，零图片拼接）。

用法：
    python verify_pptx.py "<导出.pptx>" --slides 22
    python verify_pptx.py "<导出.pptx>" --slides 22 --expect "RTX 5060" "0.071" "3.59"
"""
import argparse
import re
import sys
import zipfile


def main() -> None:
    ap = argparse.ArgumentParser(description="校验 PPTX 页数/文本/媒体/关键内容")
    ap.add_argument("pptx", help="PPTX 文件路径")
    ap.add_argument("--slides", type=int, default=None, help="期望的幻灯片页数")
    ap.add_argument(
        "--expect", nargs="*", default=[],
        help="必须出现的关键词列表（在任一页文本中命中即通过）",
    )
    args = ap.parse_args()

    failures: list[str] = []
    with zipfile.ZipFile(args.pptx) as z:
        names = z.namelist()
        slide_files = sorted(
            (n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
            key=lambda n: int(re.search(r"\d+", n.split("/")[-1]).group()),
        )
        media_files = [n for n in names if n.startswith("ppt/media/")]

        all_text = ""
        per_slide_counts: dict[str, int] = {}
        for sf in slide_files:
            xml = z.read(sf).decode("utf-8", errors="replace")
            texts = re.findall(r"<a:t>([^<]*)</a:t>", xml)
            per_slide_counts[sf] = len(texts)
            all_text += "".join(texts)

    total_slides = len(slide_files)
    total_texts = sum(per_slide_counts.values())

    print(f"幻灯片页数     : {total_slides}")
    print(f"文本节点总数   : {total_texts}")
    print(f"图片素材数     : {len(media_files)}")
    if media_files:
        print(f"  media 明细   : {media_files}")
    empty_slides = [sf for sf, c in per_slide_counts.items() if c == 0]
    if empty_slides:
        print(f"空文本页       : {empty_slides}")

    if args.slides is not None and total_slides != args.slides:
        failures.append(f"页数不符：期望 {args.slides}，实际 {total_slides}")
    if len(media_files) != 0:
        failures.append(f"存在图片素材（违反全元素可编辑要求）：{len(media_files)} 个")
    if total_texts == 0:
        failures.append("未提取到任何可编辑文本")
    if empty_slides:
        failures.append(f"以下页没有任何文本节点：{empty_slides}")
    for kw in args.expect:
        if kw not in all_text:
            failures.append(f"关键内容缺失：{kw!r}")

    if failures:
        print("\n[FAIL] 校验未通过：")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\n[PASS] 校验通过：页数、可编辑文本、零图片拼接均符合要求")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
