// stub for ssh/createSSHSession
export class SSHSessionError extends Error {}
export async function createSSHSession(opts) {
  throw new SSHSessionError('SSH sessions not implemented in this build');
}
export async function createLocalSSHSession(opts) {
  throw new SSHSessionError('SSH sessions not implemented in this build');
}
export default { createSSHSession, createLocalSSHSession, SSHSessionError };
