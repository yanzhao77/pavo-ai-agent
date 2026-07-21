import sys
sys.stdout.reconfigure(encoding="utf-8")

# Update user-guide.md
content = open("docs/user-guide.md", "r", encoding="utf-8").read()
marker = "## 6. 常见问题"
if marker in content:
    idx = content.find(marker)
    insert = "\n---\n\n## 5. MCP 客户端集成（v2.3 新增）\n\n### 5.1 MCP Server 简介\n\nPavo AI Agent v2.3 新增了 MCP Server 层，使 AI 编程工具可以直接调用 Pavo 的能力。\n\n### 5.2 可用工具（12 个）\n\n| 工具 | 说明 |\n|------|------|\n| pavo_create_project | 创建项目启动管线 |\n| pavo_get_project | 获取项目数据 |\n| pavo_list_projects | 获取项目列表 |\n| pavo_generate_storyboard | 重新生成模块 |\n| pavo_save_memory | 保存用户偏好 |\n| pavo_search_memory | 检索历史记忆 |\n| pavo_list_memories | 列出所有记忆 |\n| pavo_delete_memory | 删除指定记忆 |\n\n### 5.3 Workflow 可视化\n\n分镜生成时界面以 SVG 管线图展示 7 个 Agent 执行状态：绿色 ✓ 成功、蓝色 ◉ 执行中、红色 ✗ 失败。点击节点查看输入/输出/耗时详情。底部时间线展示各 Agent 耗时比例。\n"
    content = content[:idx] + insert + content[idx:]
    open("docs/user-guide.md", "w", encoding="utf-8").write(content)
    print("OK: user-guide.md updated")
else:
    print("Marker not found")

# Update user-guide-en.md
content2 = open("docs/user-guide-en.md", "r", encoding="utf-8").read()
marker2 = "## 6. FAQ"
if marker2 in content2:
    idx2 = content2.find(marker2)
    insert2 = "\n---\n\n## 5. MCP Client Integration (v2.3 New)\n\n### 5.1 Available Tools (12)\n\n| Tool | Description |\n|------|-------------|\n| pavo_create_project | Create project & start pipeline |\n| pavo_get_project | Get project data |\n| pavo_list_projects | List projects |\n| pavo_generate_storyboard | Regenerate module |\n| pavo_save_memory | Save user preferences |\n| pavo_search_memory | Search memories |\n| pavo_list_memories | List all memories |\n| pavo_delete_memory | Delete memory |\n\n### 5.2 Workflow Visualization\n\nThe pipeline graph shows 7 agents with color-coded status: green (completed), blue (running), red (failed). Click any node to see details. Timeline at bottom shows duration proportions.\n"
    content2 = content2[:idx2] + insert2 + content2[idx2:]
    open("docs/user-guide-en.md", "w", encoding="utf-8").write(content2)
    print("OK: user-guide-en.md updated")
else:
    print("Marker2 not found")
