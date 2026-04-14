export function initContextCollapse() {}
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
