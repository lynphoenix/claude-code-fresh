// Stub for bun:bundle — selectively enables feature flags with real implementations
// Flags set to true have complete source code in src/; false flags are stubs/unimplemented.

const ENABLED_FEATURES = new Set([
  // ── Remote / Connectivity ──────────────────────────────────────────────────
  'BRIDGE_MODE',        // replBridge.ts, bridgeMain.ts (10k+ lines)
  'DIRECT_CONNECT',     // cc:// URL handler → RemoteSessionManager
  'SSH_REMOTE',         // claude ssh → teleport.tsx (1225 lines)
  'COORDINATOR_MODE',   // coordinatorMode.ts (369 lines)
  'CCR_MIRROR',         // Claude Code Remote mirror mode
  'UDS_INBOX',          // Unix domain socket inbox

  // ── KAIROS / Assistant ─────────────────────────────────────────────────────
  'KAIROS',             // claude assistant (remote viewer) — needs index.js + gate.js stubs
  'KAIROS_BRIEF',       // kairos brief mode

  // ── Voice ─────────────────────────────────────────────────────────────────
  'VOICE_MODE',         // voice.ts, useVoice.ts, useVoiceIntegration.tsx

  // ── Session / Context ──────────────────────────────────────────────────────
  'BG_SESSIONS',        // background sessions
  'PROACTIVE',          // proactive suggestions
  'CONTEXT_COLLAPSE',   // context collapse service
  'TRANSCRIPT_CLASSIFIER', // auto mode state
  'AGENT_MEMORY_SNAPSHOT', // snapshot update dialog

  // ── Tools & Features ──────────────────────────────────────────────────────
  'CHICAGO_MCP',        // claude.ai MCP integration
  'LODESTONE',          // lodestone feature
  'UPLOAD_USER_SETTINGS', // settings upload
  'WEB_BROWSER_TOOL',   // web browser tool hint
  'ABLATION_BASELINE',  // ablation baseline (env-gated)
  'WORKFLOW_SCRIPTS',   // workflow tool
  'TEAMMEM',            // team memory
]);

export function feature(flag) {
  return ENABLED_FEATURES.has(flag);
}

export default { feature };
