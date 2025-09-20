import type { TranscribeResponse, ChatResponse, ApiError } from '../types/api';
import { ErrorHandler, sleep } from './errorHandler';
import { ENV_CONFIG } from '../config/environment';
import { AudioProcessor } from './audioProcessor';
import { responseCache } from './cache';

class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private audioProcessor: AudioProcessor;

  constructor() {
    this.baseUrl = ENV_CONFIG.API_URL;
    this.timeout = ENV_CONFIG.API_TIMEOUT;
    this.audioProcessor = AudioProcessor.getInstance();
  }

  private async fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorData: ApiError;
      try {
        errorData = await response.json();
      } catch {
        errorData = {
          detail: `HTTP ${response.status}: ${response.statusText}`,
          status: response.status
        };
      }
      
      const error = new Error(errorData.detail) as any;
      error.status = response.status;
      error.data = errorData;
      throw error;
    }

    return response.json();
  }

  async transcribeAudio(audioBlob: Blob, retryAttempts = ENV_CONFIG.RETRY_ATTEMPTS): Promise<TranscribeResponse> {
    try {
      // Check cache first
      const audioHash = await responseCache.createHash(audioBlob);
      const cachedResult = responseCache.getCachedTranscription(audioHash);
      
      if (cachedResult) {
        console.log('Using cached transcription');
        return { transcript: cachedResult };
      }

      // Log audio processing info
      const originalSize = audioBlob.size;
      console.log(`Processing audio - Original: ${(originalSize / 1024).toFixed(1)}KB`);

      // Apply audio processing
      let processedBlob = audioBlob;
      
      // Apply light noise reduction for better transcription
      processedBlob = await this.audioProcessor.applyNoiseReduction(processedBlob);
      
      // Only compress larger files to preserve quality for short recordings
      if (originalSize > 200 * 1024) { // Only compress files larger than 200KB
        console.log('Applying compression for large file...');
        processedBlob = await this.audioProcessor.compressAudio(processedBlob, 0.95);
      } else {
        console.log('Skipping compression for small file to preserve quality');
      }
      
      const finalSize = processedBlob.size;
      const compressionRatio = Math.round(((originalSize - finalSize) / originalSize) * 100);
      const sizeChange = finalSize > originalSize ? 'increase' : 'reduction';
      console.log(`Audio processed - Final: ${(finalSize / 1024).toFixed(1)}KB (${Math.abs(compressionRatio)}% ${sizeChange})`);

      const formData = new FormData();
      formData.append('file', processedBlob, 'recording.wav');

      for (let attempt = 0; attempt <= retryAttempts; attempt++) {
        try {
          const response = await this.fetchWithTimeout(`${this.baseUrl}/transcribe`, {
            method: 'POST',
            body: formData,
          });

          const result = await this.handleResponse<TranscribeResponse>(response);
          
          // Cache the result
          responseCache.cacheTranscription(audioHash, result.transcript);
          
          return result;
        } catch (error) {
          const appError = ErrorHandler.handleApiError(error, 'transcription');
          
          if (attempt === retryAttempts || !ErrorHandler.shouldRetry(appError, attempt, retryAttempts)) {
            throw appError;
          }

          // Wait before retrying
          await sleep(ErrorHandler.getRetryDelay(attempt));
        }
      }

      throw ErrorHandler.handleApiError(new Error('Max retries exceeded'), 'transcription');
    } catch (error) {
      if (error && typeof error === 'object' && 'type' in error) {
        throw error; // Re-throw AppError
      }
      throw ErrorHandler.handleApiError(error, 'transcription');
    }
  }

  async sendChatMessage(message: string, retryAttempts = ENV_CONFIG.RETRY_ATTEMPTS): Promise<ChatResponse> {
    try {
      // Check cache first
      const messageHash = await responseCache.createHash(message);
      const cachedResult = responseCache.getCachedChatResponse(messageHash);
      
      if (cachedResult) {
        console.log('Using cached chat response');
        return { response: cachedResult };
      }

      for (let attempt = 0; attempt <= retryAttempts; attempt++) {
        try {
          const response = await this.fetchWithTimeout(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
          });

          const result = await this.handleResponse<ChatResponse>(response);
          
          // Cache the result
          responseCache.cacheChatResponse(messageHash, result.response);
          
          return result;
        } catch (error) {
          const appError = ErrorHandler.handleApiError(error, 'chat');
          
          if (attempt === retryAttempts || !ErrorHandler.shouldRetry(appError, attempt, retryAttempts)) {
            throw appError;
          }

          // Wait before retrying
          await sleep(ErrorHandler.getRetryDelay(attempt));
        }
      }

      throw ErrorHandler.handleApiError(new Error('Max retries exceeded'), 'chat');
    } catch (error) {
      if (error && typeof error === 'object' && 'type' in error) {
        throw error; // Re-throw AppError
      }
      throw ErrorHandler.handleApiError(error, 'chat');
    }
  }

  async healthCheck(): Promise<{ message: string }> {
    try {
      const response = await this.fetchWithTimeout(`${this.baseUrl}/`, {
        method: 'GET',
      });

      return await this.handleResponse<{ message: string }>(response);
    } catch (error) {
      throw ErrorHandler.handleApiError(error, 'health');
    }
  }
}

export const apiClient = new ApiClient();
