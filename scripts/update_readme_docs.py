import sys
sys.stdout.reconfigure(encoding="utf-8")

# Update README.md project structure to include mcp_server
content = open("README.md", "r", encoding="utf-8").read()

# Add v2.3 note to project structure
readme_docs_td = '<tr><td><a href="docs/technical-documentation-en.md">Technical Documentation</a></td><td>Architecture, code walkthrough, API reference, deployment</td><td>English</td></tr>'
readme_docs_after = '<tr><td><a href="docs/technical-documentation-en.md">Technical Documentation</a></td><td>Architecture, code walkthrough, API reference, deployment</td><td>English</td></tr>\n<tr><td><a href="docs/技术开发计划文档_v2.3.md">v2.3 开发计划</a></td><td>Memory + RAG 技术开发计划（审核通过）</td><td>中文</td></tr>'
if readme_docs_td in content:
    content = content.replace(readme_docs_td, readme_docs_after)
    open("README.md", "w", encoding="utf-8").write(content)
    print("OK: README.md updated")
else:
    print("Pattern not found in README.md")

# Update README_EN.md similarly
content2 = open("README_EN.md", "r", encoding="utf-8").read()
en_docs_td = '<tr><td><a href="docs/technical-documentation.md">详细技术文档</a></td><td>系统架构、代码详解、API 文档、部署指南</td><td>中文</td></tr>'
en_docs_after = '<tr><td><a href="docs/technical-documentation.md">详细技术文档</a></td><td>系统架构、代码详解、API 文档、部署指南</td><td>中文</td></tr>\n<tr><td><a href="docs/技术开发计划文档_v2.3.md">v2.3 Dev Plan</a></td><td>Memory + RAG implementation plan (reviewed)</td><td>Chinese</td></tr>'
if en_docs_td in content2:
    content2 = content2.replace(en_docs_td, en_docs_after)
    open("README_EN.md", "w", encoding="utf-8").write(content2)
    print("OK: README_EN.md updated")
else:
    print("Pattern not found in README_EN.md")
