#!/usr/bin/env python3
"""提取 Word docx 的全文与表格，输出为结构化纯文本。

用途：把正式报告/论文 docx 转成可直接核对数据的纯文本（含表格逐行）。
无第三方依赖，仅用标准库解析 OOXML。

用法：
    python extract_docx_text.py "<报告.docx>"               # 输出到 stdout
    python extract_docx_text.py "<报告.docx>" -o report.txt  # 输出到文件
"""
import argparse
import sys
import zipfile
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def para_text(p: ET.Element) -> str:
    """拼接一个段落内所有 w:t 文本。"""
    return "".join(t.text or "" for t in p.iter(f"{{{W_NS}}}t"))


def extract(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find("w:body", NS)
    if body is None:
        raise SystemExit(f"错误：{path} 中未找到文档主体，请确认是有效的 .docx 文件")

    lines: list[str] = []
    for el in body:
        tag = el.tag.split("}")[1]
        if tag == "p":
            txt = para_text(el)
            if txt.strip():
                lines.append(txt)
        elif tag == "tbl":
            lines.append("[表格]")
            for row in el.findall("w:tr", NS):
                cells = [
                    " ".join(para_text(p) for p in tc.findall("w:p", NS)).strip()
                    for tc in row.findall("w:tc", NS)
                ]
                lines.append(" | ".join(cells))
            lines.append("[/表格]")
        # 分节符/目录等结构元素静默跳过
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="提取 docx 全文与表格为纯文本")
    ap.add_argument("docx", help="docx 文件路径")
    ap.add_argument("-o", "--output", help="输出文本路径（缺省打印到 stdout）")
    args = ap.parse_args()

    text = extract(args.docx)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"已提取 {len(text)} 字符 -> {args.output}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
