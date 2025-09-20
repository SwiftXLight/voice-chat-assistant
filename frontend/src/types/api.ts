// API Response Types
export interface TranscribeResponse {
  transcript: string;
}

export interface ChatResponse {
  response: string;
}

export interface ApiError {
  detail: string;
  status?: number;
  timestamp?: string;
}

// Error Types
export const ErrorType = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  API_ERROR: 'API_ERROR',
  MICROPHONE_ERROR: 'MICROPHONE_ERROR',
  TRANSCRIPTION_ERROR: 'TRANSCRIPTION_ERROR',
  CHAT_ERROR: 'CHAT_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

export type ErrorType = typeof ErrorType[keyof typeof ErrorType];

export interface AppError {
  type: ErrorType;
  message: string;
  originalError?: Error;
  retryable?: boolean;
}

// API Configuration is now in config/environment.ts
