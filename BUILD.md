# 编译说明 — claude-code 单机构建

本项目基于 claude-code v2.1.88 源码，使用 esbuild 替代原生 Bun 进行编译，并通过 stub 填补 feature-gated 模块，最终生成可在 Node.js 18+ 上运行的单文件 CLI。

## 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 编译
python3 build_single.py --root .

# 3. 打补丁
python3 patch_single.py ./dist/cli_single.js

# 4. 运行（需设置 API Key 或兼容端点）
export ANTHROPIC_API_KEY=sk-ant-xxx
node dist/cli_single_patched.js --print "hello"
```

使用 MiniMax 等兼容端点：

```bash
export ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
export ANTHROPIC_AUTH_TOKEN=your-token
export ANTHROPIC_MODEL=MiniMax-M2.7
node dist/cli_single_patched.js --print "hello"
```

启用 WebSearch（需要 Tavily API Key，免费注册：https://tavily.com）：

```bash
export TAVILY_API_KEY=tvly-xxx
node dist/cli_single_patched.js
```

## 环境要求

| 依赖 | 版本 |
|------|------|
| Node.js | >= 18 |
| Python | >= 3.8 |
| npm | >= 9 |

## 编译流程详解

### build_single.py — 四个步骤

**Step 1: 源码变换**

- 运行 `scripts/prepare-src.mjs` 处理 TypeScript 导入
- 将 `feature('FLAG')` 替换为 `true`/`false`（20 个 flag 设为 true，其余设为 false）
- 将 `MACRO.VERSION` 等编译期常量替换为字面量

启用的 feature flags（20 个）：

```
BRIDGE_MODE, COORDINATOR_MODE, DIRECT_CONNECT, SSH_REMOTE,
KAIROS, KAIROS_BRIEF, VOICE_MODE, BG_SESSIONS, PROACTIVE,
CONTEXT_COLLAPSE, TRANSCRIPT_CLASSIFIER, AGENT_MEMORY_SNAPSHOT,
CHICAGO_MCP, LODESTONE, UPLOAD_USER_SETTINGS, WEB_BROWSER_TOOL,
ABLATION_BASELINE, TEAMMEM, UDS_INBOX, CCR_MIRROR
```

**Step 2: 添加 stub 文件**

原始源码有 115 个 feature-gated 模块在发布包中没有实现，esbuild 无法消除其引用。`build_single.py` 会在 `src/` 下写入 29 个关键 stub（其中 7 个需要真实方法实现，其余为空 stub）：

| Stub | 原因 |
|------|------|
| `proactive/index.js` | PROACTIVE flag 启用后需要 `isProactiveActive`、`setContextBlocked` 等 |
| `services/contextCollapse/index.js` | CONTEXT_COLLAPSE 启用后需要 `applyCollapsesIfNeeded`、`isWithheldPromptTooLong` 等 |
| `services/contextCollapse/persist.js` | 同上，需要 `restoreFromEntries` |
| `utils/udsMessaging.js` | UDS_INBOX 启用后需要 `getDefaultUdsSocketPath`、`setOnEnqueue` 等 |
| `utils/taskSummary.js` | 工具调用时需要 `shouldGenerateTaskSummary`、`maybeGenerateTaskSummary` |
| `services/sessionTranscript/sessionTranscript.js` | 需要 `writeSessionTranscriptSegment`、`flushOnDateChange` |
| `ssh/createSSHSession.js` | SSH_REMOTE 启用后需要 `createSSHSession`（此 stub 抛出 not available 错误） |
| 其余 22 个 | 返回空实现，对应 feature=false 的死代码路径（服务器、Bridge、WebBrowser UI 等） |

> **注意**：`write_stub()` 只在文件不存在时创建。如果 `src/` 下已有文件，不会覆盖。

**Step 3: esbuild 打包**

```
esbuild src/entrypoints/cli.tsx \
  --bundle --platform=node --target=node18 --format=esm \
  --outfile=dist/cli_single.js
```

外部化（不打包）的模块：`bun:ffi`、`sharp`、`@ant/claude-for-chrome-mcp`、`@ant/computer-use-*`、Bedrock/Vertex/Foundry SDK、`color-diff-napi`、OTel exporters 等。

输出：`dist/cli_single.js`（约 22.3 MB）

**Step 4: 后处理**

- stub `color-diff-napi`（native 模块，不可打包）
- stub `@ant/claude-for-chrome-mcp`（Anthropic 内部包）
- stub `@ant/computer-use-*`（Anthropic 内部包）
- 修复 `BROWSER_TOOLS = void 0` → `[]`

### patch_single.py — 运行时补丁

对 `cli_single.js` 进行 7 项补丁，输出 `cli_single_patched.js`：

| 补丁 | 内容 |
|------|------|
| P1 | 允许在任意目录读取配置文件（去掉路径限制） |
| P2 | 禁用 GrowthBook 网络请求（`isGrowthBookEnabled` 返回 false） |
| P3a | 移除 `/v1/messages?beta=true` 中的 `?beta=true` |
| P3b | 移除 count_tokens 端点的 `?beta=true` |
| P4b | `BROWSER_TOOLS = void 0` → `[]`（双重保险） |
| P4c | 在流式解析器中添加 `thinking_delta` 的 no-op case |
| P5 | WebFetch：绕过 `api.anthropic.com` 域名黑名单预检，任意域名均可抓取 |
| P6 | WebSearch：call() 替换为 Tavily API，支持所有 API provider |

> **P4a 注意**：P4a 补丁已被移除。原先试图将 `content[0].text` 替换为 `.find(b => b.type==="text")` 以兼容 MiniMax 思考块，但该替换会错误地修改 `message.message.content[0].text` 中的子串，导致语法错误。MiniMax 实测无需此补丁。

## 扩展工具配置

### Computer Use（截图 + 鼠标 + 键盘）

`tools/computer-use-mcp.py` 是一个 Python MCP server，替代 Anthropic 内部 native 包，通过 `pyautogui` + `scrot` 实现桌面控制。

**安装：**
```bash
pip install mcp pyautogui Pillow
# Linux 截图需要 scrot：apt install scrot
```

**MCP 配置（加入 `~/.claude.json`）：**
```json
{
  "mcpServers": {
    "computer-use": {
      "command": "python3",
      "args": ["/path/to/tools/computer-use-mcp.py"]
    }
  }
}
```

提供三个工具：`computer_screenshot`、`computer_mouse`、`computer_keyboard`。

### 浏览器自动化（替代 Chrome MCP）

`@ant/claude-for-chrome-mcp` 是 Anthropic 内部未发布包，用微软官方 `@playwright/mcp` 替代，详见 `tools/browser-mcp-setup.md`。

**安装：**
```bash
npm install -g @playwright/mcp
npx playwright install chromium
```

**MCP 配置：**
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

去掉 `--headless` 可看到真实浏览器窗口。`browser` 适合网页自动化（有 DOM 感知），`computer-use` 适合桌面 GUI 控制。

### WebSearch（Tavily）

WebSearch 工具的 `call()` 已替换为 Tavily API，不再依赖 Anthropic 服务端搜索，任何 API provider 均可使用。

```bash
export TAVILY_API_KEY=tvly-xxx   # 免费注册：https://tavily.com
```

不设置 `TAVILY_API_KEY` 时，工具会出现但调用时返回错误提示。

## 原理说明

### 为什么不用 Bun

原始构建使用 Bun 的两个编译期特性：

1. **`feature('FLAG')`**：Bun 在编译时将其解析为 `true`/`false` 并消除死代码。我们通过字符串替换模拟，但 esbuild 的 DCE 能力弱于 Bun。
2. **`MACRO.VERSION`**：Bun 的 `--define` 在编译时注入。我们通过 Python 字符串替换模拟。

### Feature Flag 启用的影响

将 feature flag 设为 `true` 意味着 esbuild 会保留对应代码分支，这些分支可能调用未发布的内部模块。因此每启用一个新 flag，就可能暴露出新的缺失方法，需要补充对应 stub。

如果遇到 `TypeError: xxx is not a function` 崩溃，通常是某个 `true`-enabled 模块的 stub 缺少对应方法。

### 已测试功能

| 功能 | 状态 |
|------|------|
| `--print` 单轮对话 | ✅ |
| 交互模式多轮对话（上下文记忆） | ✅ |
| 工具调用（Write + Bash） | ✅ |
| MiniMax-M2.7 思考块兼容 | ✅ |
| WebFetch（任意域名） | ✅ |
| WebSearch（Tavily） | ✅ |
| Computer Use（MCP server） | ✅ |
| 浏览器自动化（Playwright MCP） | ✅ |

## 目录结构

```
claude-code-fresh/
├── src/                    # TypeScript 源码（含 stub .js 文件）
│   ├── proactive/index.js  # PROACTIVE stub
│   ├── services/contextCollapse/
│   │   ├── index.js        # CONTEXT_COLLAPSE stub
│   │   └── persist.js      # persist stub
│   ├── utils/
│   │   ├── taskSummary.js  # task summary stub
│   │   └── udsMessaging.js # UDS stub
│   └── services/sessionTranscript/
│       └── sessionTranscript.js
├── build_single.py         # 主编译脚本
├── patch_single.py         # 运行时补丁脚本
├── scripts/
│   └── prepare-src.mjs     # 源码预处理
├── tools/
│   ├── computer-use-mcp.py     # Computer Use MCP server（截图/鼠标/键盘）
│   └── browser-mcp-setup.md   # Playwright MCP 配置指南
├── dist/                   # 编译产物（gitignore）
│   ├── cli_single.js       # esbuild 输出
│   └── cli_single_patched.js  # 最终可运行文件
└── node_modules/           # npm 依赖（gitignore）
```

## 常见问题

**Q: 遇到 `TypeError: xxx is not a function`**

某个 feature-enabled 模块的 stub 缺少方法。在 `dist/cli_single_patched.js` 中搜索 `init_xxx`，找到对应 src 文件，在 stub 里添加缺失的方法，重新编译。

**Q: 遇到语法错误 `SyntaxError: Unexpected token`**

通常是 patch 脚本的字符串替换匹配了不该替换的位置。检查 `patch_single.py` 中的正则是否用了负向后顾 `(?<!\.)` 防止匹配属性链。

**Q: WebFetch 报 `Unable to verify if domain is safe`**

P5 补丁已绕过此预检，重新运行 `patch_single.py` 确认补丁已应用。

**Q: WebSearch 不工作**

检查 `TAVILY_API_KEY` 环境变量是否已设置。免费 key 在 https://tavily.com 注册获取。

**Q: 编译后文件多大**

约 22.3 MB（ESM 格式，未压缩），包含约 2930 个 `__esm` 模块（1939 来自 src/，991 来自 70 个 npm 包）。
