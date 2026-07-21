# -*- coding: utf-8 -*-
import os, sys

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'doc.md')

sections = {}

sections['h1'] = '# AI \u89c6\u9891\u751f\u6210 Agent \u2014 \u6280\u672f\u5f00\u53d1\u6587\u6863'
sections['subtitle'] = '> \u57fa\u4e8e Pavo AI \u5e73\u53f0\u300c\u7238\u7238\u7684\u5341\u5757\u94b1\u300d\u89c6\u9891\u9879\u76ee\u5206\u6790\uff0c\u5efa\u7acb\u5728 Agnes AI \u7edf\u4e00\u6a21\u578b\u7f51\u5173\u4e0a\u7684 AI \u89c6\u9891\u751f\u6210 Agent \u7cfb\u7edf'
sections['version'] = '> \u7248\u672c\uff1av2.0 | \u65e5\u671f\uff1a2026-07-12'

content_parts = [
    sections['h1'], '', sections['subtitle'], sections['version'], '',
    '---', '',
    '## 1. \u9879\u76ee\u6982\u8ff0', '',
    '### 1.1 \u76ee\u6807', '',
    '\u6784\u5efa\u4e00\u4e2a AI Agent \u7cfb\u7edf\uff0c\u80fd\u591f\u6839\u636e\u7528\u6237\u8f93\u5165\u7684\u6545\u4e8b\u521b\u610f\u6216\u4e00\u53e5\u8bdd\u9700\u6c42\uff0c\u81ea\u52a8\u751f\u6210\u5b8c\u6574\u89c6\u9891\u9879\u76ee\u3002'
]

def write():
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content_parts))
    print(f'Written ({os.path.getsize(OUTPUT)} bytes)')

if __name__ == '__main__':
    write()
