#!/usr/bin/env python3
"""
patch_single.py v4 — All patches including P4 for MiniMax thinking block compatibility.

Patches:
  P1: Allow config reading in any directory
  P2: Disable GrowthBook feature flag network requests
  P3a/b: Remove beta query param from API URLs
  P4: MiniMax thinking block compatibility — fix --print output

Usage: python3 patch_single.py [/build/dist/cli_single.js]
Output: /build/dist/cli_single_patched.js (same dir, _patched suffix)
"""
import re, sys, os

IN  = sys.argv[1] if len(sys.argv) > 1 else '/build/dist/cli_single.js'
OUT = IN.replace('cli_single.js', 'cli_single_patched.js')

with open(IN, encoding='utf-8') as f:
    content = f.read()

patches = []

def patch(name, old, new, count=1):
    global content
    n = content.count(old)
    if n == 0:
        print(f'  ✗ {name}: pattern not found')
        return False
    if count == 1 and n > 1:
        print(f'  ⚠ {name}: {n} occurrences (expected 1), replacing first')
    content = content.replace(old, new, count)
    patches.append(name)
    print(f'  ✓ {name}')
    return True

def patch_re(name, pattern, replacement, flags=0, count=0):
    global content
    new_content = re.sub(pattern, replacement, content, count=count, flags=flags)
    if new_content == content:
        print(f'  ✗ {name}: regex not matched')
        return False
    content = new_content
    patches.append(name)
    print(f'  ✓ {name}')
    return True

# ── P1: Allow config reading in any directory ─────────────────────────────────
patch('P1: allow config read anywhere',
    'if (!configReadingAllowed &&',
    'if (false &&')

# ── P2: Disable GrowthBook feature flag network requests ─────────────────────
# Replace the function body to return false, keeping the original function name
# (so all callers still work). Use regex to match the function body.
patch_re('P2: disable GrowthBook (return false)',
    r'function isGrowthBookEnabled\(\)\s*\{[^}]*\}',
    'function isGrowthBookEnabled() { return false; }')

# ── P3: Remove beta query params from API URLs ────────────────────────────────
patch('P3a: remove beta from /v1/messages',
    '"/v1/messages?beta=true"',
    '"/v1/messages"')
patch('P3b: remove beta from count_tokens',
    '"/v1/messages/count_tokens?beta=true"',
    '"/v1/messages/count_tokens"')

# ── P4: MiniMax thinking block compatibility ──────────────────────────────────
# MiniMax-M2.7 always returns thinking blocks before text blocks.
# Claude Code's --print mode extracts text from the response, but may grab
# content[0].text which for MiniMax would be the thinking block (no .text field),
# resulting in undefined/empty output.
#
# Fix strategy:
# 4a) content[0].text → find first text-type content block
# 4b) Ensure BROWSER_TOOLS is [] not void 0 (already done in build step but belt+suspenders)

# P4a: content[0].text → first text block
# This pattern appears where --print extracts the response text
# IMPORTANT: Use regex with negative lookbehind to avoid replacing property accesses.
# E.g., 'message.message.content[0].text' should NOT be modified — only standalone
# var references like 'message.content[0].text' where 'message' is the root object.
# Strategy: replace VAR.content[0].text only when NOT preceded by a dot (property chain).
p4a_applied = False
for var in ['msg', 'message', 'result', 'response', 'block']:
    # (?<!\.) ensures the var is not preceded by a dot (i.e., not a chained property)
    pattern = rf'(?<!\.)(?<![a-zA-Z0-9_]){re.escape(var)}\.content\[0\]\.text'
    replacement = f'({var}.content.find(function(b){{return b.type==="text";}})||{{}}).text'
    new_content, n = re.subn(pattern, replacement, content)
    if n > 0:
        content = new_content
        patches.append(f'P4a: {var}.content[0].text → find first text block ({n} occurrences)')
        print(f'  \u2713 P4a: {var}.content[0].text \u2192 find first text block ({n} occurrences)')
        p4a_applied = True

if not p4a_applied:
    print('  - P4a: no content[0].text patterns found (may not be needed)')

# P4b: BROWSER_TOOLS safety (belt+suspenders from build step postprocess)
content = content.replace('var BROWSER_TOOLS = void 0;', 'var BROWSER_TOOLS = [];')
content = content.replace('var BROWSER_TOOLS2 = void 0;', 'var BROWSER_TOOLS2 = [];')
print('  ✓ P4b: BROWSER_TOOLS = [] (no-op if already set)')

# P4c: Handle thinking blocks gracefully in streaming accumulator
# If the bundle has a switch/if on content block type that doesn't handle "thinking",
# add a passthrough case. Try multiple patterns.
p4c_patterns = [
    # Pattern: text_delta case in a switch (esbuild arrow form)
    (r'case "text_delta":', 'case "thinking_delta": case "input_thinking_delta": case "text_delta":',
     'P4c: add thinking_delta as no-op in switch'),
    # Pattern: if block_type === text
    (r'if\s*\((\w+)\.type\s*===\s*"text"\s*\)\s*\{',
     r'if(\1.type==="thinking"){/* thinking block: skip */}else if(\1.type==="text"){',
     'P4c-alt: add thinking passthrough in if-type-text'),
]
for old_pat, new_pat, name in p4c_patterns:
    if re.search(old_pat, content):
        new_content = re.sub(old_pat, new_pat, content, count=1)
        if new_content != content:
            content = new_content
            patches.append(name)
            print(f'  ✓ {name}')
            break
else:
    print('  ✗ P4c: no streaming accumulator pattern matched')

# ── Write output ──────────────────────────────────────────────────────────────
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(content)

size = os.path.getsize(OUT) / 1024 / 1024
print(f'\nPatches: {len(patches)} applied')
print(f'Output:  {OUT} ({size:.1f} MB)')
