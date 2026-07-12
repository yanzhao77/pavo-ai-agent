# -*- coding: utf-8 -*-
import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_cn.md')
with open(out, 'w', encoding='utf-8') as f:
    f.write('# 测试中文\n\n这是一段中文测试。\n')
print('done')
