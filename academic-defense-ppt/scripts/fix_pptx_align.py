# -*- coding: utf-8 -*-
"""PPTX 对齐属性回填：Ardot 导出丢失 algn/anchor，从画布结构按树序回填。
用法: python fix_pptx_align.py <pptx> <read_a.jsonl> <read_b.jsonl> <read_c.jsonl>
"""
import json, re, shutil, sys, zipfile, os

ALGN_MAP = {'LEFT': None, 'CENTER': 'ctr', 'RIGHT': 'r', 'JUSTIFY': 'just'}
ANCH_MAP = {'TOP': None, 'CENTER': 'ctr', 'BOTTOM': 'b'}

pptx_path = sys.argv[1]
dumps = sys.argv[2:5]

# ---- 1. 提取画布对齐意图: {slide_no: [ (algn, anchor, text), ... ]} 按树序 ----
intent = {}
for f in dumps:
    for line in open(f, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get('type') != 'SLIDE' or not obj.get('name', '').startswith('P'):
            continue
        slide_no = int(obj['name'].split()[0][1:])
        seq = []

        def walk(n):
            if n.get('type') == 'TEXT':
                seq.append((ALGN_MAP.get(n.get('textAlignHorizontal', 'LEFT')),
                            ANCH_MAP.get(n.get('textAlignVertical', 'TOP')),
                            (n.get('characters') or '')[:24]))
            for c in n.get('children') or []:
                if isinstance(c, dict):
                    walk(c)
        for c in obj.get('children') or []:
            if isinstance(c, dict):
                walk(c)
        intent[slide_no] = seq

total = sum(len(v) for v in intent.values())
need = sum(1 for v in intent.values() for e in v if e[0] or e[1])
print(f'画布文本节点: {total}，需回填对齐: {need}')

# ---- 2. 逐页回填 ----
tmp = pptx_path + '.tmp'
zin = zipfile.ZipFile(pptx_path, 'r')
zout = zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED)
fixed_pages, mismatch = [], []

SP_RE = re.compile(r'<p:sp>.*?</p:sp>', re.S)

def fix_slide(xml, seq):
    it = iter(seq)
    used = [0]
    def repl(m):
        s = m.group(0)
        if '<a:t>' not in s:
            return s
        try:
            algn, anchor, txt = next(it)
        except StopIteration:
            return s
        used[0] += 1
        if algn:
            if '<a:pPr' in s:
                # 已有 pPr：无 algn 则注入
                def add_algn(pm):
                    tag = pm.group(0)
                    return tag if 'algn=' in tag else tag[:-1] + f' algn="{algn}"/>' if tag.endswith('/>') else tag[:-1] + f' algn="{algn}">'
                s2 = re.sub(r'<a:pPr[^>]*/?>', add_algn, s, count=1)
            else:
                s2 = s.replace('<a:r>', f'<a:pPr algn="{algn}"/><a:r>', 1)
                if s2 == s:  # 没有 run 的情况
                    s2 = s.replace('</a:txBody>', f'<a:pPr algn="{algn}"/></a:txBody>', 1)
            s = s2
        if anchor:
            if 'anchor=' in s:
                s = re.sub(r'anchor="\w+"', f'anchor="{anchor}"', s, count=1)
            else:
                s = re.sub(r'<a:bodyPr', f'<a:bodyPr anchor="{anchor}"', s, count=1)
        return s
    out = SP_RE.sub(repl, xml)
    return out, used[0]

for item in zin.infolist():
    data = zin.read(item.filename)
    m = re.fullmatch(r'ppt/slides/slide(\d+)\.xml', item.filename)
    if m:
        page = int(m.group(1))
        if page in intent:
            xml = data.decode('utf-8')
            out, used = fix_slide(xml, intent[page])
            if used != len(intent[page]):
                mismatch.append((page, used, len(intent[page])))
            else:
                fixed_pages.append(page)
            data = out.encode('utf-8')
    zout.writestr(item, data)
zout.close()
zin.close()
shutil.move(tmp, pptx_path)

print('回填完成页:', len(fixed_pages), '/ 22')
if mismatch:
    print('!! 数量不匹配(跳过判断):', mismatch)

# ---- 3. 校验 ----
z = zipfile.ZipFile(pptx_path)
from collections import Counter
for sn in ['ppt/slides/slide1.xml', 'ppt/slides/slide6.xml', 'ppt/slides/slide19.xml']:
    xml = z.read(sn).decode('utf-8')
    print(sn, 'algn:', dict(Counter(re.findall(r'algn=\"(\w+)\"', xml))))
