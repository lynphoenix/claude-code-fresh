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
