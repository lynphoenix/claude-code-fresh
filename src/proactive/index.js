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
