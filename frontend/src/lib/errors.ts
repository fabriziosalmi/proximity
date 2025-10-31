/**
 * Error message sanitization utility
 * Maps backend error messages to safe, user-friendly messages
 * Prevents information disclosure while providing helpful feedback
 */

import * as Sentry from '@sentry/sveltekit';
import { logger } from './logger';

// Map of known error patterns to safe messages
const SAFE_ERROR_MESSAGES: Record<string, string> = {
	// User already exists errors
	'user_already_exists': 'An account with this username already exists',
	'email_already_exists': 'An account with this email already exists',
	'email_in_use': 'This email address is already registered',

	// Validation errors
	'invalid_email': 'Please provide a valid email address',
	'invalid_username': 'Username must be 3-30 characters (letters, numbers, underscores)',
	'password_too_weak': 'Password must be at least 8 characters with a mix of letters, numbers, and symbols',
	'password_too_short': 'Password must be at least 8 characters',
	'email_required': 'Email address is required',
	'username_required': 'Username is required',
	'password_required': 'Password is required',

	// Field-specific errors
	'username': 'This username is not available',
	'password': 'Password does not meet security requirements',
	'email': 'Please enter a valid email address',

	// Generic errors
	'validation_error': 'Please check your input and try again',
	'bad_request': 'Invalid request. Please check your input.',
	'unauthorized': 'Invalid credentials. Please try again.',
	'forbidden': 'You do not have permission to perform this action',
	'not_found': 'The requested resource was not found',
	'server_error': 'A server error occurred. Please try again later.',
	'network_error': 'Network connection failed. Please check your internet and try again.',
	'timeout': 'Request timed out. Please try again.',
};

/**
 * Sanitize backend error messages to prevent information disclosure
 * Maps known errors to safe messages, logs unknown errors for investigation
 */
export function sanitizeError(error: string | Record<string, any>, fieldName?: string): string {
	// Handle object errors (from form validation)
	if (typeof error === 'object' && error !== null) {
		// If it's an array (multiple errors), take the first
		if (Array.isArray(error)) {
			return sanitizeError(error[0], fieldName);
		}

		// If it has a message property
		if (error.message && typeof error.message === 'string') {
			return sanitizeError(error.message, fieldName);
		}

		// Try to extract any string value
		const firstValue = Object.values(error).find((v) => typeof v === 'string');
		if (firstValue) {
			return sanitizeError(firstValue as string, fieldName);
		}

		// Fallback for unknown object
		Sentry.captureMessage(`Unknown error object format: ${JSON.stringify(error)}`);
		return 'An error occurred. Please try again.';
	}

	// Ensure we're working with a string
	const errorStr = String(error).toLowerCase().trim();

	// Check for known error patterns
	for (const [key, safeMessage] of Object.entries(SAFE_ERROR_MESSAGES)) {
		if (errorStr.includes(key.toLowerCase())) {
			logger.debug(`Error mapped: "${key}" → safe message`);
			return safeMessage;
		}
	}

	// Check if it's a field-specific error
	if (fieldName) {
		const fieldKey = fieldName.toLowerCase();
		if (SAFE_ERROR_MESSAGES[fieldKey]) {
			return SAFE_ERROR_MESSAGES[fieldKey];
		}
	}

	// For unknown errors, log them for investigation but show generic message
	logger.warn('Unknown error encountered:', { originalError: error, field: fieldName });
	Sentry.captureMessage(`Unknown error: ${error}`, 'warning');

	return 'An error occurred. Please try again or contact support.';
}

/**
 * Parse validation errors from API response
 * Handles dj-rest-auth format: { detail: [{ loc: [...], msg: "..." }, ...] }
 */
export function parseValidationErrors(
	errorData: any
): Record<string, string> {
	const validationErrors: Record<string, string> = {};

	if (!errorData) {
		return validationErrors;
	}

	// Handle dj-rest-auth validation error format
	if (Array.isArray(errorData.detail)) {
		errorData.detail.forEach((err: any) => {
			if (err.loc && Array.isArray(err.loc) && err.msg) {
				// Get the field name (last element of location)
				const fieldName = err.loc[err.loc.length - 1];
				// Sanitize the error message
				const safeMessage = sanitizeError(err.msg, fieldName);
				validationErrors[fieldName] = safeMessage;
			}
		});
		return validationErrors;
	}

	// Handle object with field-level errors
	if (typeof errorData === 'object') {
		for (const [field, message] of Object.entries(errorData)) {
			validationErrors[field] = sanitizeError(message as string, field);
		}
		return validationErrors;
	}

	// Fallback: return generic error
	validationErrors.general = sanitizeError(errorData);
	return validationErrors;
}

/**
 * Get a safe error message for display
 * Combines multiple error messages or returns single error
 */
export function getDisplayError(validationErrors: Record<string, string>): string {
	const nonGeneralErrors = Object.entries(validationErrors)
		.filter(([key]) => key !== 'general')
		.map(([, message]) => message);

	if (nonGeneralErrors.length > 0) {
		// Show up to 3 errors, abbreviated
		return nonGeneralErrors.slice(0, 3).join('. ') + (nonGeneralErrors.length > 3 ? '...' : '');
	}

	return validationErrors.general || 'An error occurred. Please try again.';
}
