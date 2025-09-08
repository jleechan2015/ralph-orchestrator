#!/usr/bin/env python3
# ABOUTME: Simple test to verify Claude adapter works with all tools
# ABOUTME: Quick validation of the implementation

import asyncio
from src.ralph_orchestrator.adapters.claude import ClaudeAdapter

async def main():
    # Create adapter
    adapter = ClaudeAdapter(verbose=False)
    
    # Test 1: Default configuration (tools restricted)
    print("Test 1: Default configuration")
    adapter.configure()
    print(f"  Enable all tools: {adapter._enable_all_tools}")
    print(f"  Allowed tools: {adapter._allowed_tools}")
    print()
    
    # Test 2: Enable all tools
    print("Test 2: Enable all native tools")
    adapter.configure(enable_all_tools=True)
    print(f"  Enable all tools: {adapter._enable_all_tools}")
    print(f"  Allowed tools: {adapter._allowed_tools}")
    print()
    
    # Test 3: Enable all tools with specific allowed list (should use the allowed list)
    print("Test 3: Enable all tools but with specific allowed list")
    adapter.configure(enable_all_tools=True, allowed_tools=["Read", "Bash"])
    print(f"  Enable all tools: {adapter._enable_all_tools}")
    print(f"  Allowed tools: {adapter._allowed_tools}")
    print()
    
    # Test 4: Quick execution test
    print("Test 4: Quick execution test with all tools")
    adapter.configure(enable_all_tools=True)
    
    response = await adapter.aexecute(
        "What is 2 + 2? Just answer with the number.",
        enable_all_tools=True
    )
    
    if response.success:
        print(f"  ✓ Execution successful")
        print(f"  Response: {response.output.strip()[:50]}")
    else:
        print(f"  ✗ Execution failed: {response.error}")
    
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())