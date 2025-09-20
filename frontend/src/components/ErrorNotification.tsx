import React, { useEffect } from 'react';
import { type AppError, ErrorType } from '../types/api';

interface ErrorNotificationProps {
  error: AppError | null;
  onDismiss: () => void;
  onRetry?: () => void;
  autoHide?: boolean;
  autoHideDelay?: number;
}

const ErrorNotification: React.FC<ErrorNotificationProps> = ({
  error,
  onDismiss,
  onRetry,
  autoHide = true,
  autoHideDelay = 5000
}) => {
  useEffect(() => {
    if (error && autoHide) {
      const timer = setTimeout(() => {
        onDismiss();
      }, autoHideDelay);

      return () => clearTimeout(timer);
    }
  }, [error, autoHide, autoHideDelay, onDismiss]);

  if (!error) return null;

  const getErrorIcon = (type: ErrorType): string => {
    switch (type) {
      case ErrorType.NETWORK_ERROR:
        return '🌐';
      case ErrorType.MICROPHONE_ERROR:
        return '🎤';
      case ErrorType.TRANSCRIPTION_ERROR:
        return '🗣️';
      case ErrorType.CHAT_ERROR:
        return '🤖';
      case ErrorType.API_ERROR:
        return '⚠️';
      default:
        return '❌';
    }
  };

  const getErrorClass = (type: ErrorType): string => {
    switch (type) {
      case ErrorType.NETWORK_ERROR:
      case ErrorType.API_ERROR:
        return 'error-warning';
      case ErrorType.MICROPHONE_ERROR:
        return 'error-info';
      default:
        return 'error-danger';
    }
  };

  return (
    <div className={`error-notification ${getErrorClass(error.type)}`}>
      <div className="error-content">
        <span className="error-icon">{getErrorIcon(error.type)}</span>
        <div className="error-text">
          <strong>Error:</strong> {error.message}
        </div>
      </div>
      
      <div className="error-actions">
        {error.retryable === true && onRetry && (
          <button onClick={onRetry} className="error-retry-btn">
            🔄 Retry
          </button>
        )}
        <button onClick={onDismiss} className="error-dismiss-btn">
          ✕
        </button>
      </div>
    </div>
  );
};

export default ErrorNotification;
