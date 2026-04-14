// KAIROS module stub
let _forced = false;
export function markAssistantForced() { _forced = true; }
export function isAssistantForced() { return _forced; }
export async function initializeAssistantTeam() { return undefined; }
export function getAssistantSystemPromptAddendum() { return ""; }
export function getAssistantActivationPath() { return undefined; }
export function isAssistantMode() { return false; }
export default { markAssistantForced, isAssistantForced, initializeAssistantTeam,
  getAssistantSystemPromptAddendum, getAssistantActivationPath, isAssistantMode };
