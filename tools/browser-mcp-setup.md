# 浏览器 MCP 配置指南

替代 `@ant/claude-for-chrome-mcp`（Anthropic 内部未发布包），使用微软官方 `@playwright/mcp`。

## 安装

```bash
npm install -g @playwright/mcp
npx playwright install chromium
```

## 配置（~/.claude.json 或项目 .mcp.json）

```json
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["@playwright/mcp", "--headless"]
    }
  }
}
```

去掉 `--headless` 可以看到真实浏览器窗口。

## 可用工具

接入后 Claude Code 可直接使用：
- 打开网页、截图
- 点击、输入、滚动
- 获取页面内容
- 填写表单、导航

## 与 Computer Use 组合使用

```json
{
  "mcpServers": {
    "computer-use": {
      "command": "python3",
      "args": ["tools/computer-use-mcp.py"]
    },
    "browser": {
      "command": "npx",
      "args": ["@playwright/mcp", "--headless"]
    }
  }
}
```

`browser` 适合网页自动化（有 DOM 感知），`computer-use` 适合桌面 GUI 控制（截图+鼠标）。
