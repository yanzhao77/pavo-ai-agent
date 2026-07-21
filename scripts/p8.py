with open("backend/mcp_server/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the current call_tool try block
old = '''    try:
        err = check_api_key()
        if err:
            return err'''

# Remove any existing guards injection  
current_middleware_line = '''    middleware = MemoryMiddleware()'''
new_middleware_block = '''    # Security: check API Key first
    err = check_api_key()
    if err:
        return err

    middleware = MemoryMiddleware()'''

# Add import
if "from .tools.guards import check_api_key" not in content:
    content = content.replace(
        "from .middleware.memory_middleware import MemoryMiddleware",
        "from .middleware.memory_middleware import MemoryMiddleware\nfrom .tools.guards import check_api_key"
    )

# Wire into call_tool
if current_middleware_line in content:
    content = content.replace(current_middleware_line, new_middleware_block)
    with open("backend/mcp_server/main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Phase 8: check_api_key wired into call_tool")
else:
    print("ERROR: Could not find middleware line")
