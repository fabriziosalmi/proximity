/**
 * Form Validation Utilities
 *
 * Provides real-time validation for form inputs with visual feedback.
 * Prevents submission of invalid data and improves UX.
 */

/**
 * Validation rules and error messages
 */
const VALIDATION_RULES = {
    // IP address validation (IPv4)
    ipv4: {
        pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
        message: 'Invalid IP address format (e.g., 192.168.1.100)'
    },

    // Hostname validation (alphanumeric + dots + hyphens)
    hostname: {
        pattern: /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
        message: 'Invalid hostname format'
    },

    // IP or hostname
    host: {
        validate: (value) => {
            return VALIDATION_RULES.ipv4.pattern.test(value) ||
                   VALIDATION_RULES.hostname.pattern.test(value);
        },
        message: 'Invalid host (must be IP address or hostname)'
    },

    // CIDR notation (e.g., 10.20.0.0/24)
    cidr: {
        pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/([0-9]|[1-2][0-9]|3[0-2])$/,
        message: 'Invalid CIDR notation (e.g., 10.20.0.0/24)'
    },

    // Port number (1-65535)
    port: {
        validate: (value) => {
            const num = parseInt(value, 10);
            return !isNaN(num) && num >= 1 && num <= 65535;
        },
        message: 'Port must be between 1 and 65535'
    },

    // Proxmox username format (user@realm)
    proxmoxUser: {
        pattern: /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+$/,
        message: 'Invalid format (e.g., root@pam or admin@pve)'
    },

    // DNS domain
    dnsDomain: {
        pattern: /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
        message: 'Invalid domain format (e.g., prox.local)'
    },

    // Positive integer
    positiveInt: {
        validate: (value) => {
            const num = parseInt(value, 10);
            return !isNaN(num) && num > 0 && Number.isInteger(num);
        },
        message: 'Must be a positive integer'
    },

    // Range validation
    range: (min, max) => ({
        validate: (value) => {
            const num = parseFloat(value);
            return !isNaN(num) && num >= min && num <= max;
        },
        message: `Must be between ${min} and ${max}`
    }),

    // Required field
    required: {
        validate: (value) => value && value.trim().length > 0,
        message: 'This field is required'
    }
};

/**
 * Field-specific validation configurations
 */
const FIELD_VALIDATIONS = {
    // Proxmox form
    'proxmoxForm.host': ['required', 'host'],
    'proxmoxForm.port': ['required', 'port'],
    'proxmoxForm.user': ['required', 'proxmoxUser'],

    // Network form
    'networkForm.lan_subnet': ['required', 'cidr'],
    'networkForm.lan_gateway': ['required', 'ipv4'],
    'networkForm.dhcp_start': ['required', 'ipv4'],
    'networkForm.dhcp_end': ['required', 'ipv4'],
    'networkForm.dns_domain': ['required', 'dnsDomain'],

    // Resources form
    'resourcesForm.lxc_memory': ['required', 'positiveInt'],
    'resourcesForm.lxc_cores': ['required', 'positiveInt'],
    'resourcesForm.lxc_disk': ['required', 'positiveInt'],
    'resourcesForm.lxc_storage': ['required']
};

/**
 * Validate a single input field
 * @param {HTMLInputElement} input - The input element to validate
 * @param {string[]} rules - Array of validation rule names
 * @returns {Object} { valid: boolean, error: string|null }
 */
function validateField(input, rules) {
    const value = input.value.trim();

    // Check required first
    if (rules.includes('required')) {
        const requiredRule = VALIDATION_RULES.required;
        if (!requiredRule.validate(value)) {
            return { valid: false, error: requiredRule.message };
        }
    }

    // Skip other validations if empty and not required
    if (!value && !rules.includes('required')) {
        return { valid: true, error: null };
    }

    // Check other rules
    for (const ruleName of rules) {
        if (ruleName === 'required') continue;

        const rule = VALIDATION_RULES[ruleName];
        if (!rule) {
            console.warn(`Unknown validation rule: ${ruleName}`);
            continue;
        }

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

/**
 * Show validation error on input field
 * @param {HTMLInputElement} input - The input element
 * @param {string} errorMessage - Error message to display
 */
function showFieldError(input, errorMessage) {
    const formGroup = input.closest('.form-group');
    if (!formGroup) return;

    // Add error class to input
    input.classList.add('error');
    input.classList.remove('success');

    // Remove existing error message
    const existingError = formGroup.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }

    // Add error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.innerHTML = `<i data-lucide="alert-circle"></i><span>${errorMessage}</span>`;

    // Insert after input or after form-help
    const formHelp = formGroup.querySelector('.form-help');
    if (formHelp) {
        formHelp.after(errorDiv);
    } else {
        input.after(errorDiv);
    }

    // Initialize Lucide icon
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

/**
 * Show validation success on input field
 * @param {HTMLInputElement} input - The input element
 */
function showFieldSuccess(input) {
    const formGroup = input.closest('.form-group');
    if (!formGroup) return;

    // Add success class to input
    input.classList.remove('error');
    input.classList.add('success');

    // Remove error message if exists
    const existingError = formGroup.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Clear validation state from input field
 * @param {HTMLInputElement} input - The input element
 */
function clearFieldValidation(input) {
    input.classList.remove('error', 'success');

    const formGroup = input.closest('.form-group');
    if (!formGroup) return;

    const existingError = formGroup.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Initialize real-time validation for a form
 * @param {string} formId - The form element ID
 */
export function initFormValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) {
        console.warn(`Form not found: ${formId}`);
        return;
    }

    // Get all inputs that need validation
    const inputs = form.querySelectorAll('input[name]:not([type="checkbox"])');

    inputs.forEach(input => {
        const fieldKey = `${formId}.${input.name}`;
        const rules = FIELD_VALIDATIONS[fieldKey];

        if (!rules) return; // Skip fields without validation rules

        // Validate on blur (when user leaves field)
        input.addEventListener('blur', () => {
            const result = validateField(input, rules);

            if (!result.valid) {
                showFieldError(input, result.error);
            } else {
                showFieldSuccess(input);
            }
        });

        // Clear validation on focus (when user enters field)
        input.addEventListener('focus', () => {
            clearFieldValidation(input);
        });

        // Re-validate on input (while typing) if already validated
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

    // Validate all fields on form submit
    form.addEventListener('submit', (e) => {
        let isValid = true;
        const firstInvalidInput = null;

        inputs.forEach(input => {
            const fieldKey = `${formId}.${input.name}`;
            const rules = FIELD_VALIDATIONS[fieldKey];

            if (!rules) return;

            const result = validateField(input, rules);

            if (!result.valid) {
                showFieldError(input, result.error);
                isValid = false;

                // Focus first invalid input
                if (!firstInvalidInput) {
                    input.focus();
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            } else {
                showFieldSuccess(input);
            }
        });

        if (!isValid) {
            e.preventDefault();
            window.showWarning?.('Please fix validation errors before saving');
        }
    });

    console.log(`✓ Validation initialized for form: ${formId}`);
}

/**
 * Validate specific DHCP range logic
 * @param {string} startIp - DHCP start IP
 * @param {string} endIp - DHCP end IP
 * @returns {Object} { valid: boolean, error: string|null }
 */
export function validateDhcpRange(startIp, endIp) {
    // Convert IP to number for comparison
    const ipToNum = (ip) => {
        const parts = ip.split('.');
        return (parseInt(parts[0]) << 24) +
               (parseInt(parts[1]) << 16) +
               (parseInt(parts[2]) << 8) +
               parseInt(parts[3]);
    };

    const startNum = ipToNum(startIp);
    const endNum = ipToNum(endIp);

    if (startNum >= endNum) {
        return {
            valid: false,
            error: 'DHCP start must be lower than DHCP end'
        };
    }

    return { valid: true, error: null };
}

/**
 * Validate IP is within subnet
 * @param {string} ip - IP address to check
 * @param {string} cidr - Subnet in CIDR notation
 * @returns {Object} { valid: boolean, error: string|null }
 */
export function validateIpInSubnet(ip, cidr) {
    // Parse CIDR
    const [subnet, maskBits] = cidr.split('/');
    const mask = parseInt(maskBits);

    // Convert IP to binary
    const ipToNum = (ipStr) => {
        const parts = ipStr.split('.');
        return (parseInt(parts[0]) << 24) +
               (parseInt(parts[1]) << 16) +
               (parseInt(parts[2]) << 8) +
               parseInt(parts[3]);
    };

    const ipNum = ipToNum(ip);
    const subnetNum = ipToNum(subnet);
    const maskNum = (0xFFFFFFFF << (32 - mask)) >>> 0;

    if ((ipNum & maskNum) !== (subnetNum & maskNum)) {
        return {
            valid: false,
            error: `IP ${ip} is not within subnet ${cidr}`
        };
    }

    return { valid: true, error: null };
}

// Export for global use (non-module)
if (typeof window !== 'undefined') {
    window.FormValidation = {
        initFormValidation,
        validateDhcpRange,
        validateIpInSubnet,
        validateField,
        showFieldError,
        showFieldSuccess,
        clearFieldValidation
    };
}
