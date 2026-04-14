#!/usr/bin/env python3
"""
Computer Use MCP Server
提供截图、鼠标控制、键盘输入三个工具，通过 MCP 协议与 Claude Code 通信
"""

import asyncio
import base64
import subprocess
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("computer-use")

def take_screenshot() -> str:
    """截图并返回 base64 编码"""
    try:
        # 优先用 scrot，没有就用 import
        result = subprocess.run(
            ["scrot", "-", "--format", "png"],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return base64.b64encode(result.stdout).decode()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        result = subprocess.run(
            ["import", "-window", "root", "png:-"],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return base64.b64encode(result.stdout).decode()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # 无显示器环境，返回空图
    from PIL import Image
    import io
    img = Image.new("RGB", (1920, 1080), color=(30, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="computer_screenshot",
            description="截取当前屏幕截图，返回 base64 编码的 PNG 图片",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="computer_mouse",
            description="控制鼠标：移动、点击、双击、右键",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["move", "click", "double_click", "right_click", "scroll"],
                        "description": "鼠标动作"
                    },
                    "x": {"type": "integer", "description": "X 坐标（像素）"},
                    "y": {"type": "integer", "description": "Y 坐标（像素）"},
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down"],
                        "description": "滚动方向（scroll 动作用）"
                    },
                    "amount": {
                        "type": "integer",
                        "description": "滚动格数",
                        "default": 3
                    }
                },
                "required": ["action", "x", "y"]
            }
        ),
        types.Tool(
            name="computer_keyboard",
            description="模拟键盘输入：输入文字或按快捷键",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["type", "key"],
                        "description": "type=输入文字，key=按下快捷键（如 ctrl+c）"
                    },
                    "text": {
                        "type": "string",
                        "description": "要输入的文字或按键名（如 ctrl+c, Return, Escape）"
                    }
                },
                "required": ["action", "text"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent]:
    if name == "computer_screenshot":
        img_b64 = take_screenshot()
        return [types.ImageContent(
            type="image",
            data=img_b64,
            mimeType="image/png"
        )]

    elif name == "computer_mouse":
        action = arguments["action"]
        x = arguments["x"]
        y = arguments["y"]
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            if action == "move":
                pyautogui.moveTo(x, y)
                return [types.TextContent(type="text", text=f"已移动鼠标到 ({x}, {y})")]
            elif action == "click":
                pyautogui.click(x, y)
                return [types.TextContent(type="text", text=f"已点击 ({x}, {y})")]
            elif action == "double_click":
                pyautogui.doubleClick(x, y)
                return [types.TextContent(type="text", text=f"已双击 ({x}, {y})")]
            elif action == "right_click":
                pyautogui.rightClick(x, y)
                return [types.TextContent(type="text", text=f"已右键点击 ({x}, {y})")]
            elif action == "scroll":
                direction = arguments.get("direction", "down")
                amount = arguments.get("amount", 3)
                clicks = amount if direction == "up" else -amount
                pyautogui.scroll(clicks, x=x, y=y)
                return [types.TextContent(type="text", text=f"已在 ({x}, {y}) 向{direction}滚动 {amount} 格")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"鼠标操作失败: {e}")]

    elif name == "computer_keyboard":
        action = arguments["action"]
        text = arguments["text"]
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            if action == "type":
                pyautogui.write(text, interval=0.02)
                return [types.TextContent(type="text", text=f"已输入文字: {text}")]
            elif action == "key":
                pyautogui.hotkey(*text.split("+"))
                return [types.TextContent(type="text", text=f"已按下按键: {text}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"键盘操作失败: {e}")]

    return [types.TextContent(type="text", text=f"未知工具: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
