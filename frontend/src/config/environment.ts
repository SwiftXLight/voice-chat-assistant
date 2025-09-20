// Environment configuration
export const ENV_CONFIG = {
  API_URL: import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000'),
  NODE_ENV: import.meta.env.MODE || 'development',
  IS_PRODUCTION: import.meta.env.PROD,
  IS_DEVELOPMENT: import.meta.env.DEV,
  
  // API Configuration
  API_TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
  
  // Audio Configuration
  MAX_RECORDING_TIME: 300000, // 5 minutes in milliseconds
  AUDIO_SAMPLE_RATE: 44100,
  
  // Error Reporting
  SENTRY_DSN: import.meta.env.VITE_SENTRY_DSN,
  
  // Feature Flags
  ENABLE_ANALYTICS: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  ENABLE_DEBUG_LOGS: import.meta.env.DEV
};

// Validate required environment variables
export const validateEnvironment = (): void => {
  const requiredVars: string[] = [];
  
  // Add any required environment variables here
  // Example: if (!ENV_CONFIG.API_URL) requiredVars.push('REACT_APP_API_URL');
  
  if (requiredVars.length > 0) {
    throw new Error(`Missing required environment variables: ${requiredVars.join(', ')}`);
  }
};

// Initialize environment validation
if (ENV_CONFIG.IS_PRODUCTION) {
  validateEnvironment();
}
