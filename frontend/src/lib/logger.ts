/**
 * 🔐 Secure Logging Utility
 *
 * This module provides environment-aware logging:
 * - Development: Logs to console for debugging
 * - Production: Sends errors to Sentry only (no console exposure)
 *
 * Purpose: Prevent sensitive information disclosure in production
 */

import * as Sentry from '@sentry/sveltekit';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  data?: any;
  timestamp: string;
}

class Logger {
  private isDev = import.meta.env.DEV;

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    const levelUpper = level.toUpperCase();
    return `[${timestamp}] [${levelUpper}] ${message}`;
  }

  debug(message: string, data?: any): void {
    if (this.isDev) {
      // Use console directly to avoid circular reference
      console.log(this.formatMessage('debug', message), data);
    }
  }

  info(message: string, data?: any): void {
    if (this.isDev) {
      // Use console directly to avoid circular reference
      console.info(this.formatMessage('info', message), data);
    }
  }

  warn(message: string, data?: any): void {
    if (this.isDev) {
      // Use console directly to avoid circular reference
      console.warn(this.formatMessage('warn', message), data);
    }
    // Also send warnings to Sentry in production
    if (!this.isDev) {
      Sentry.captureMessage(message, 'warning');
    }
  }

  error(message: string, error?: Error | any): void {
    // Always send to Sentry
    if (error instanceof Error) {
      Sentry.captureException(error);
    } else {
      Sentry.captureMessage(message, 'error');
    }

    // Only log to console in development
    if (this.isDev) {
      // Use console directly to avoid circular reference
      console.error(this.formatMessage('error', message), error);
    }
  }

  /**
   * Sanitize sensitive data before logging
   * Useful for stripping passwords, tokens, etc.
   */
  sanitize(obj: any, keys: string[] = ['password', 'token', 'secret', 'key']): any {
    if (!obj || typeof obj !== 'object') return obj;

    const sanitized = JSON.parse(JSON.stringify(obj));

    function scrub(o: any) {
      if (Array.isArray(o)) {
        o.forEach(scrub);
      } else if (o && typeof o === 'object') {
        for (const key of Object.keys(o)) {
          if (keys.some(k => key.toLowerCase().includes(k.toLowerCase()))) {
            o[key] = '[REDACTED]';
          } else {
            scrub(o[key]);
          }
        }
      }
    }

    scrub(sanitized);
    return sanitized;
  }
}

export const logger = new Logger();
