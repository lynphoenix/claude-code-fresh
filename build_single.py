#!/usr/bin/env python3
"""
build_single.py v4 — Single-system build for claude-code with selective feature flags.

Steps:
  1. transform src/ (prepare-src.mjs + selective feature()=true/false + MACRO.X)
  2. add stub files to src/ (feature-gated modules not yet implemented)
  3. esbuild bundle
  4. post-process (stub native/internal packages)

Usage: python3 build_single.py [--root /build]
Output: dist/cli_single.js
"""
import os, re, subprocess, sys

ROOT = sys.argv[sys.argv.index('--root') + 1] if '--root' in sys.argv else '/build'
SRC  = os.path.join(ROOT, 'src')
OUT  = os.path.join(ROOT, 'dist', 'cli_single.js')

VERSION = '2.1.88'

MACRO_MAP = {
    'MACRO.VERSION':              f"'{VERSION}'",
    'MACRO.BUILD_TIME':           "''",
    'MACRO.FEEDBACK_CHANNEL':     "'https://github.com/anthropics/claude-code/issues'",
    'MACRO.ISSUES_EXPLAINER':     "'https://github.com/anthropics/claude-code/issues/new/choose'",
    'MACRO.FEEDBACK_CHANNEL_URL': "'https://github.com/anthropics/claude-code/issues'",
    'MACRO.ISSUES_EXPLAINER_URL': "'https://github.com/anthropics/claude-code/issues/new/choose'",
    'MACRO.NATIVE_PACKAGE_URL':   "'@anthropic-ai/claude-code'",
    'MACRO.PACKAGE_URL':          "'@anthropic-ai/claude-code'",
    'MACRO.VERSION_CHANGELOG':    "''",
}

# Features to enable (get `true`); all others get `false` → dead code eliminated
FEATURES_TRUE = {
    'BRIDGE_MODE', 'COORDINATOR_MODE', 'DIRECT_CONNECT', 'SSH_REMOTE',
    'KAIROS', 'KAIROS_BRIEF', 'VOICE_MODE', 'BG_SESSIONS', 'PROACTIVE',
    'CONTEXT_COLLAPSE', 'TRANSCRIPT_CLASSIFIER', 'AGENT_MEMORY_SNAPSHOT',
    'CHICAGO_MCP', 'LODESTONE', 'UPLOAD_USER_SETTINGS', 'WEB_BROWSER_TOOL',
    'ABLATION_BASELINE', 'TEAMMEM', 'UDS_INBOX', 'CCR_MIRROR',
}

FEATURE_RE = re.compile(r"""\bfeature\s*\(\s*['"]([A-Z_]+)['"]\s*\)""")

def replace_feature(m):
    flag = m.group(1)
    return 'true' if flag in FEATURES_TRUE else 'false'

# ── Step 1: transform src/ in-place ──────────────────────────────────────────
def step_transform_src():
    print('Step 1: transforming src/ (selective feature()=true/false, MACRO.X->literals)...')

    result = subprocess.run(
        ['node', 'scripts/prepare-src.mjs'],
        cwd=ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'  WARNING: prepare-src.mjs exited {result.returncode}: {result.stderr[:200]}')
    else:
        last = result.stdout.strip().splitlines()
        print(f'  prepare-src.mjs: {last[-1] if last else "ok"}')

    patched = 0
    for dirpath, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d != 'node_modules']
        for fname in files:
            if not (fname.endswith('.ts') or fname.endswith('.tsx')):
                continue
            path = os.path.join(dirpath, fname)
            with open(path, encoding='utf-8') as f:
                content = f.read()
            orig = content
            content = FEATURE_RE.sub(replace_feature, content)
            for k, v in MACRO_MAP.items():
                content = content.replace(k, v)
            if content != orig:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                patched += 1

    enabled = sorted(FEATURES_TRUE)
    print(f'  feature() replacements: patched {patched} files')
    print(f'  enabled flags ({len(enabled)}): {", ".join(enabled)}')

# ── Step 2: add stub files to src/ ───────────────────────────────────────────
def step_add_stubs():
    print('Step 2: adding stub files to src/...')

    def write_stub(rel, content):
        dst = os.path.join(SRC, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            with open(dst, 'w') as f:
                f.write(content)
            print(f'  created: src/{rel}')

    # ── KAIROS / Assistant feature stubs ────────────────────────────────────
    # These modules are needed when KAIROS=true but lack a real implementation
    write_stub('assistant/index.js', '''\
export function markAssistantForced() {}
export function isAssistantForced() { return false; }
export function initializeAssistantTeam() {}
export function getAssistantSystemPromptAddendum() { return ''; }
export function getAssistantActivationPath() { return null; }
export function isAssistantMode() { return false; }
export default {};
''')
    write_stub('assistant/gate.js', '''\
export function isKairosEnabled() { return true; }
export default { isKairosEnabled };
''')
    write_stub('assistant/sessionDiscovery.js', '''\
export async function discoverAssistantSessions() { return []; }
export default { discoverAssistantSessions };
''')
    write_stub('assistant/AssistantSessionChooser.js', '''\
export default function AssistantSessionChooser() {}
''')
    write_stub('commands/assistant/index.js', '''\
export default {};
''')
    write_stub('screens/assistant/AssistantSessionChooser.tsx', '''\
export default function AssistantSessionChooser() { return null; }
''')

    # ── UI stubs ─────────────────────────────────────────────────────────────
    write_stub('components/agents/SnapshotUpdateDialog.tsx', '''\
export default function SnapshotUpdateDialog() { return null; }
''')
    write_stub('tools/TungstenTool/TungstenLiveMonitor.js', '''\
export default function TungstenLiveMonitor() {}
''')
    write_stub('proactive/useProactive.js', '''\
export function useProactive() { return null; }
export default { useProactive };
''')
    write_stub('tools/WebBrowserTool/WebBrowserPanel.js', '''\
export default function WebBrowserPanel() { return null; }
''')

    # ── BG_SESSIONS: background session CLI commands ─────────────────────────
    write_stub('cli/bg.js', '''\
export function psHandler() {}
export function logsHandler() {}
export function attachHandler() {}
export function killHandler() {}
export async function handleBgFlag() { return false; }
export default { psHandler, logsHandler, attachHandler, killHandler, handleBgFlag };
''')

    # ── Server / COORDINATOR_MODE / DIRECT_CONNECT stubs ─────────────────────
    write_stub('server/server.js', '''\
export async function startServer() { throw new Error('server not implemented'); }
export default { startServer };
''')
    write_stub('server/sessionManager.js', '''\
export class SessionManager { constructor() {} }
export default { SessionManager };
''')
    write_stub('server/backends/dangerousBackend.js', '''\
export function createDangerousBackend() { throw new Error('not implemented'); }
export default { createDangerousBackend };
''')
    write_stub('server/serverBanner.js', '''\
export function printServerBanner() {}
export default { printServerBanner };
''')
    write_stub('server/serverLog.js', '''\
export function serverLog() {}
export default { serverLog };
''')
    write_stub('server/lockfile.js', '''\
export function acquireLockfile() {}
export function releaseLockfile() {}
export default { acquireLockfile, releaseLockfile };
''')
    write_stub('server/connectHeadless.js', '''\
export async function connectHeadless() { throw new Error('not implemented'); }
export default { connectHeadless };
''')
    write_stub('server/parseConnectUrl.js', '''\
export function parseConnectUrl(url) { return {}; }
export default { parseConnectUrl };
''')

    # ── Permission UI stubs ──────────────────────────────────────────────────
    write_stub('components/permissions/MonitorPermissionRequest/MonitorPermissionRequest.js', '''\
export default function MonitorPermissionRequest() { return null; }
''')
    write_stub('components/permissions/ReviewArtifactPermissionRequest/ReviewArtifactPermissionRequest.js', '''\
export default function ReviewArtifactPermissionRequest() { return null; }
''')

    # ── SSH_REMOTE: createSSHSession ─────────────────────────────────────────
    write_stub('ssh/createSSHSession.js', '''\
export class SSHSessionError extends Error {
  constructor(message) { super(message); this.name = 'SSHSessionError'; }
}
export async function createSSHSession(opts) {
  throw new SSHSessionError('SSH sessions not available in this build');
}
export async function createLocalSSHSession(opts) {
  throw new SSHSessionError('SSH sessions not available in this build');
}
export default { SSHSessionError, createSSHSession, createLocalSSHSession };
''')

    # ── Dream skill stub ─────────────────────────────────────────────────────
    write_stub('skills/bundled/dream.js', '''\
export function registerDreamSkill() {}
export default { registerDreamSkill };
''')

    # ── PROACTIVE: proactive module stub ──────────────────────────────────────────────
    write_stub('proactive/index.js', """\
let _active = false;
let _paused = false;
let _blocked = false;
export function isProactiveActive() { return _active; }
export function isProactivePaused() { return _paused; }
export function activateProactive(reason) { _active = true; _paused = false; }
export function deactivateProactive() { _active = false; }
export function pauseProactive() { _paused = true; }
export function resumeProactive() { _paused = false; }
export function setContextBlocked(v) { _blocked = v; }
export default { isProactiveActive, isProactivePaused, activateProactive, deactivateProactive, pauseProactive, resumeProactive, setContextBlocked };
""")

    # ── CONTEXT_COLLAPSE: contextCollapse stubs ─────────────────────────────────────
    write_stub('services/contextCollapse/index.js', """export function initContextCollapse() {}
export function resetContextCollapse() {}
export function isContextCollapseEnabled() { return false; }
export async function applyCollapsesIfNeeded(messages, opts, querySource) {
  return { messages: messages || [], collapsed: false };
}
export function recoverFromOverflow(messages) { return messages; }
export function push(entry) {}
export function filter(fn) { return []; }
export function getStats() { return {}; }
export const collapseContext = async () => null;
export function isWithheldPromptTooLong(message, isPromptTooLongMessage, querySource) { return false; }
export default { initContextCollapse, resetContextCollapse, isContextCollapseEnabled, applyCollapsesIfNeeded, recoverFromOverflow, push, filter, getStats, collapseContext, isWithheldPromptTooLong };
""")
    write_stub('services/contextCollapse/persist.js', """export async function restoreFromEntries(entries) { return []; }
export async function persistEntries(entries) {}
export default { restoreFromEntries, persistEntries };
""")

    # ── TASK_SUMMARY + SESSION_TRANSCRIPT stubs ─────────────────────────────────────
    write_stub('utils/taskSummary.js', """export function shouldGenerateTaskSummary() { return false; }
export async function maybeGenerateTaskSummary(opts) {}
export default { shouldGenerateTaskSummary, maybeGenerateTaskSummary };
""")
    write_stub('services/sessionTranscript/sessionTranscript.js', """export async function writeSessionTranscriptSegment(segment) {}
export async function flushOnDateChange() {}
export default { writeSessionTranscriptSegment, flushOnDateChange };
""")

    # ── UDS_INBOX: udsMessaging stub ──────────────────────────────────────────────
    write_stub('utils/udsMessaging.js', """\
import os from 'os';
import path from 'path';
export function getDefaultUdsSocketPath() {
  return path.join(os.tmpdir(), 'claude-uds-messaging.sock');
}
export async function startUdsMessaging(socketPath, opts) {}
export function getUdsMessagingSocketPath() { return null; }
export function stopUdsMessaging() {}
export function setOnEnqueue(fn) {}
export default { getDefaultUdsSocketPath, startUdsMessaging, getUdsMessagingSocketPath, stopUdsMessaging, setOnEnqueue };
""")

    # ── verifyContent: references missing .md files ──────────────────────────
    os.makedirs(os.path.join(SRC, 'skills/bundled/verify/examples'), exist_ok=True)
    for md in ['SKILL.md', 'examples/cli.md', 'examples/server.md']:
        p = os.path.join(SRC, 'skills/bundled/verify', md)
        if not os.path.exists(p):
            open(p, 'w').close()
    with open(os.path.join(SRC, 'skills/bundled/verifyContent.ts'), 'w') as f:
        f.write('const cliMd = ""\nconst serverMd = ""\nconst skillMd = ""\n')
        f.write('export const SKILL_MD = ""\n')
        f.write('export const SKILL_FILES: Record<string, string> = {}\n')
        f.write('export { cliMd, serverMd, skillMd }\n')
        f.write('export default { cliMd, serverMd, skillMd }\n')
    print('  created: verifyContent.ts + .md stubs')

# ── Step 3: esbuild ───────────────────────────────────────────────────────────
def step_esbuild():
    print('Step 3: running esbuild...')
    os.makedirs(os.path.join(ROOT, 'dist'), exist_ok=True)
    entry   = os.path.join(SRC, 'entrypoints/cli.tsx')
    esbuild = os.path.join(ROOT, 'node_modules/.bin/esbuild')
    # IMPORTANT: use double quotes around node:module to prevent esbuild stripping quotes
    banner  = 'import{createRequire as _ccRequire}from"node:module";const require=_ccRequire(import.meta.url);'

    externals = [
        'bun:ffi', 'sharp',
        # Anthropic internal / unpublished
        '@ant/claude-for-chrome-mcp',
        '@anthropic-ai/mcpb',
        # Computer use (native + internal)
        '@ant/computer-use-input',
        '@ant/computer-use-mcp',
        '@ant/computer-use-swift',
        # Optional cloud SDKs (dynamically imported)
        '@anthropic-ai/bedrock-sdk', '@anthropic-ai/foundry-sdk', '@anthropic-ai/vertex-sdk',
        '@azure/identity',
        '@aws-sdk/client-sts', '@aws-sdk/client-bedrock',
        # Native binary modules
        'color-diff-napi', 'modifiers-napi',
        # Audio capture (native)
        'audio-capture-napi',
        # Optional OTel exporters
        '@opentelemetry/exporter-*', '@opentelemetry/instrumentation',
    ]

    cmd = [
        esbuild, entry,
        '--bundle', '--platform=node', '--target=node18', '--format=esm',
        f'--outfile={OUT}', '--allow-overwrite',
        f'--banner:js={banner}',
    ] + [f'--external:{e}' for e in externals]

    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    for line in (result.stdout + result.stderr).splitlines():
        if any(kw in line for kw in ('ERROR', 'Done', 'mb', 'WARNING')):
            print(f'  {line.strip()}')
    if result.returncode != 0:
        print('  FULL ERRORS:\n' + result.stderr[:3000])
        sys.exit(1)

# ── Step 4: post-process ──────────────────────────────────────────────────────
def step_postprocess():
    print('Step 4: post-processing bundle...')
    with open(OUT, encoding='utf-8') as f:
        lines = f.readlines()

    # remove duplicate banner (esbuild occasionally emits it twice)
    if len(lines) > 1 and lines[0].startswith('import{createRequire') and lines[1].startswith('import{createRequire'):
        lines.pop(1)
        print('  removed duplicate banner')

    content = ''.join(lines)

    # add missing __create helper (esbuild occasionally omits it)
    if 'var __create = Object.create' not in content:
        content = content.replace(
            'var __defProp = Object.defineProperty;',
            'var __create = Object.create;\nvar __defProp = Object.defineProperty;'
        )
        print('  added __create helper')

    # ── color-diff-napi: native module, cannot be bundled ─────────────────────
    # Use regex to match any import form (may be multi-line)
    color_re = re.compile(
        r'import\s*\{[^}]*(?:ColorDiff|ColorFile|nativeGetSyntaxTheme)[^}]*\}\s*from\s*"color-diff-napi";',
        re.DOTALL
    )
    if color_re.search(content):
        content = color_re.sub(
            '// color-diff-napi: native module (void 0 in original bundle too)\n'
            'var ColorDiff = void 0;\nvar ColorFile = void 0;\nvar nativeGetSyntaxTheme = void 0;',
            content
        )
        print('  stubbed color-diff-napi')

    # ── @ant/claude-for-chrome-mcp: Anthropic internal, unpublished ───────────
    chrome_re = re.compile(r'import\s*\{([^}]+)\}\s*from\s*"@ant/claude-for-chrome-mcp";')
    seen_chrome = set()
    def chrome_stub(m):
        names = [n.strip().split(' as ')[-1].strip() for n in m.group(1).split(',') if n.strip()]
        decls = [f'var {n} = [];' for n in names if n not in seen_chrome and not seen_chrome.add(n)]
        return '// @ant/claude-for-chrome-mcp: internal Anthropic package\n' + '\n'.join(decls)
    if '"@ant/claude-for-chrome-mcp"' in content:
        content = chrome_re.sub(chrome_stub, content)
        print('  stubbed @ant/claude-for-chrome-mcp')

    # ── @ant/computer-use-*: Anthropic internal packages ──────────────────────
    cu_re = re.compile(r'import\s*\{([^}]+)\}\s*from\s*"(@ant/computer-use-[^"]+)";')
    seen_cu = set()
    def cu_stub(m):
        names = [n.strip().split(' as ')[-1].strip() for n in m.group(1).split(',') if n.strip()]
        pkg = m.group(2)
        decls = [f'var {n} = void 0;' for n in names if n not in seen_cu and not seen_cu.add(n)]
        return f'// {pkg}: Anthropic internal package\n' + '\n'.join(decls)
    if '@ant/computer-use-' in content:
        new_content = cu_re.sub(cu_stub, content)
        if new_content != content:
            content = new_content
            print('  stubbed @ant/computer-use-* packages')

    # ── Fix BROWSER_TOOLS: must be [] not void 0 (used at module init time) ───
    content = content.replace('var BROWSER_TOOLS = void 0;', 'var BROWSER_TOOLS = [];')
    content = content.replace('var BROWSER_TOOLS2 = void 0;', 'var BROWSER_TOOLS2 = [];')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(content)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'Building single-system bundle  src → {OUT}\n')
    step_transform_src()
    step_add_stubs()
    step_esbuild()
    step_postprocess()
    size = os.path.getsize(OUT) / 1024 / 1024
    print(f'\nDone! {OUT} ({size:.1f} MB)')
    print('Next: python3 patch_single.py && python3 patch_p4.py')
