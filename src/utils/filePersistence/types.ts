export const DEFAULT_UPLOAD_CONCURRENCY = 4
export const FILE_COUNT_LIMIT = 100
export const OUTPUTS_SUBDIR = outputs
export type FailedPersistence = { file: string; error: string }
export type FilesPersistedEventData = { files: string[] }
export type PersistedFile = { path: string }
export type TurnStartTime = number
