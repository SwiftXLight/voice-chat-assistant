import { ErrorType, type AppError } from '../types/api';

export class ErrorHandler {
  static createError(type: ErrorType, message: string, originalError?: Error, retryable = false): AppError {
    return {
      type,
      message,
      originalError,
      retryable
    };
  }

  static handleApiError(error: any, context: string): AppError {
    // Network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return this.createError(
        ErrorType.NETWORK_ERROR,
        'Unable to connect to the server. Please check your internet connection.',
        error,
        true
      );
    }

    // API response errors
    if (error.status) {
      switch (error.status) {
        case 400:
          return this.createError(
            ErrorType.API_ERROR,
            'Invalid request. Please try again.',
            error,
            false
          );
        case 401:
          return this.createError(
            ErrorType.API_ERROR,
            'Authentication failed. Please check your API key.',
            error,
            false
          );
        case 429:
          return this.createError(
            ErrorType.API_ERROR,
            'Too many requests. Please wait a moment and try again.',
            error,
            true
          );
        case 500:
          return this.createError(
            ErrorType.API_ERROR,
            'Server error. Please try again later.',
            error,
            true
          );
        default:
          return this.createError(
            ErrorType.API_ERROR,
            `Server error (${error.status}). Please try again.`,
            error,
            true
          );
      }
    }

    // Context-specific errors
    if (context === 'transcription') {
      return this.createError(
        ErrorType.TRANSCRIPTION_ERROR,
        'Failed to transcribe audio. Please try recording again.',
        error,
        true
      );
    }

    if (context === 'chat') {
      return this.createError(
        ErrorType.CHAT_ERROR,
        'Failed to get AI response. Please try again.',
        error,
        true
      );
    }

    // Default error
    return this.createError(
      ErrorType.UNKNOWN_ERROR,
      'An unexpected error occurred. Please try again.',
      error,
      true
    );
  }

  static handleMicrophoneError(error: any): AppError {
    if (error.name === 'NotAllowedError') {
      return this.createError(
        ErrorType.MICROPHONE_ERROR,
        'Microphone access denied. Please allow microphone permissions and try again.',
        error,
        false
      );
    }

    if (error.name === 'NotFoundError') {
      return this.createError(
        ErrorType.MICROPHONE_ERROR,
        'No microphone found. Please connect a microphone and try again.',
        error,
        false
      );
    }

    if (error.name === 'NotSupportedError') {
      return this.createError(
        ErrorType.MICROPHONE_ERROR,
        'Your browser does not support audio recording. Please try a different browser.',
        error,
        false
      );
    }

    return this.createError(
      ErrorType.MICROPHONE_ERROR,
      'Failed to access microphone. Please check your microphone settings.',
      error,
      true
    );
  }

  static getRetryDelay(attempt: number): number {
    // Exponential backoff: 1s, 2s, 4s, 8s...
    return Math.min(1000 * Math.pow(2, attempt), 10000);
  }

  static shouldRetry(error: AppError, attempt: number, maxAttempts: number): boolean {
    return error.retryable === true && attempt < maxAttempts;
  }
}

export const sleep = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));
