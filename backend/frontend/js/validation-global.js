/**
 * Form Validation System - Global Version
 *
 * Non-module version for use in app.js
 * Provides real-time validation with visual feedback
 */

(function() {
    'use strict';

    /**
     * Validation rules
     */
    const VALIDATION_RULES = {
        ipv4: {
            pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
            message: 'Invalid IP address format (e.g., 192.168.1.100)'
        },
        hostname: {
            pattern: /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
            message: 'Invalid hostname format'
        },
        host: {
            validate: (value) => {
                return VALIDATION_RULES.ipv4.pattern.test(value) ||
                       VALIDATION_RULES.hostname.pattern.test(value);
            },
            message: 'Invalid host (must be IP address or hostname)'
        },
        cidr: {
            pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$/,
            message: 'Invalid CIDR notation (e.g., 10.20.0.0/24)'
        },
        port: {
            validate: (value) => {
                const num = parseInt(value, 10);
                return !isNaN(num) && num >= 1 && num <= 65535;
            },
            message: 'Port must be between 1 and 65535'
        },
        proxmoxUser: {
            pattern: /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+$/,
            message: 'Invalid format (e.g., root@pam)'
        },
        dnsDomain: {
            pattern: /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
            message: 'Invalid domain format (e.g., prox.local)'
        },
        positiveInt: {
            validate: (value) => {
                const num = parseInt(value, 10);
                return !isNaN(num) && num > 0 && Number.isInteger(num);
            },
            message: 'Must be a positive integer'
        },
        required: {
            validate: (value) => value && value.trim().length > 0,
            message: 'This field is required'
        }
    };

    /**
     * Field validations
     */
    const FIELD_VALIDATIONS = {
        'proxmoxForm.host': ['required', 'host'],
        'proxmoxForm.port': ['required', 'port'],
        'proxmoxForm.user': ['required', 'proxmoxUser'],
        'networkForm.lan_subnet': ['required', 'cidr'],
        'networkForm.lan_gateway': ['required', 'ipv4'],
        'networkForm.dhcp_start': ['required', 'ipv4'],
        'networkForm.dhcp_end': ['required', 'ipv4'],
        'networkForm.dns_domain': ['required', 'dnsDomain'],
        'resourcesForm.lxc_memory': ['required', 'positiveInt'],
        'resourcesForm.lxc_cores': ['required', 'positiveInt'],
        'resourcesForm.lxc_disk': ['required', 'positiveInt'],
        'resourcesForm.lxc_storage': ['required']
    };

    function validateField(input, rules) {
        const value = input.value.trim();

        if (rules.includes('required')) {
            const requiredRule = VALIDATION_RULES.required;
            if (!requiredRule.validate(value)) {
                return { valid: false, error: requiredRule.message };
            }
        }

        if (!value && !rules.includes('required')) {
            return { valid: true, error: null };
        }

        for (const ruleName of rules) {
            if (ruleName === 'required') continue;

            const rule = VALIDATION_RULES[ruleName];
            if (!rule) continue;

            let isValid = false;
            if (rule.pattern) {
                isValid = rule.pattern.test(value);
            } else if (rule.validate) {
                isValid = rule.validate(value);
            }

            if (!isValid) {
                return { valid: false, error: rule.message };
            }
        }

        return { valid: true, error: null };
    }

    function showFieldError(input, errorMessage) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;

        input.classList.add('error');
        input.classList.remove('success');

        const existingError = formGroup.querySelector('.form-error');
        if (existingError) existingError.remove();

        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.innerHTML = `<i data-lucide="alert-circle"></i><span>${errorMessage}</span>`;

        const formHelp = formGroup.querySelector('.form-help');
        if (formHelp) {
            formHelp.after(errorDiv);
        } else {
            input.after(errorDiv);
        }

        if (window.lucide) window.lucide.createIcons();
    }

    function showFieldSuccess(input) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;

        input.classList.remove('error');
        input.classList.add('success');

        const existingError = formGroup.querySelector('.form-error');
        if (existingError) existingError.remove();
    }

    function clearFieldValidation(input) {
        input.classList.remove('error', 'success');

        const formGroup = input.closest('.form-group');
        if (!formGroup) return;

        const existingError = formGroup.querySelector('.form-error');
        if (existingError) existingError.remove();
    }

    function initFormValidation(formId) {
        const form = document.getElementById(formId);
        if (!form) {
            console.warn(`Form not found: ${formId}`);
            return;
        }

        const inputs = form.querySelectorAll('input[name]:not([type="checkbox"])');

        inputs.forEach(input => {
            const fieldKey = `${formId}.${input.name}`;
            const rules = FIELD_VALIDATIONS[fieldKey];

            if (!rules) return;

            input.addEventListener('blur', () => {
                const result = validateField(input, rules);
                if (!result.valid) {
                    showFieldError(input, result.error);
                } else {
                    showFieldSuccess(input);
                }
            });

            input.addEventListener('focus', () => {
                clearFieldValidation(input);
            });

            input.addEventListener('input', () => {
                if (input.classList.contains('error') || input.classList.contains('success')) {
                    const result = validateField(input, rules);
                    if (!result.valid) {
                        showFieldError(input, result.error);
                    } else {
                        showFieldSuccess(input);
                    }
                }
            });
        });

        form.addEventListener('submit', (e) => {
            let isValid = true;
            let firstInvalidInput = null;

            inputs.forEach(input => {
                const fieldKey = `${formId}.${input.name}`;
                const rules = FIELD_VALIDATIONS[fieldKey];

                if (!rules) return;

                const result = validateField(input, rules);

                if (!result.valid) {
                    showFieldError(input, result.error);
                    isValid = false;

                    if (!firstInvalidInput) {
                        firstInvalidInput = input;
                    }
                } else {
                    showFieldSuccess(input);
                }
            });

            if (!isValid) {
                e.preventDefault();
                if (firstInvalidInput) {
                    firstInvalidInput.focus();
                    firstInvalidInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                if (window.showWarning) {
                    window.showWarning('Please fix validation errors before saving');
                }
            }
        });

        console.log(`✓ Validation initialized for form: ${formId}`);
    }

    // Expose globally
    window.initFormValidation = initFormValidation;
    window.validateField = validateField;
    window.showFieldError = showFieldError;
    window.showFieldSuccess = showFieldSuccess;
    window.clearFieldValidation = clearFieldValidation;

})();
