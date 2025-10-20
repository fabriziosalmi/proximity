#!/usr/bin/env python3
"""
Script to update action button styles in apps page to match flip button aesthetic
"""

import re

file_path = "frontend/src/routes/apps/+page.svelte"

with open(file_path, 'r') as f:
    content = f.read()

# Define replacements for button classes
replacements = [
    # Stop button (yellow warning)
    (
        r'class="flex flex-1 items-center justify-center gap-2 rounded-lg border border-rack-primary/30 bg-rack-darker px-3 py-2 text-sm text-yellow-400 transition-colors hover:bg-rack-darker/80 disabled:opacity-50"',
        'class="action-btn action-btn-warning flex-1"'
    ),
    # Restart/Reload button (blue primary)
    (
        r'class="flex flex-1 items-center justify-center gap-2 rounded-lg border border-rack-primary/30 bg-rack-darker px-3 py-2 text-sm text-rack-primary transition-colors hover:bg-rack-darker/80 disabled:opacity-50"',
        'class="action-btn action-btn-primary flex-1"'
    ),
    # Clone button (cyan info)
    (
        r'class="flex flex-1 items-center justify-center gap-2 rounded-lg border border-blue-500/30 bg-blue-500/10 px-3 py-2 text-sm text-blue-400 transition-colors hover:bg-blue-500/20 disabled:opacity-50"',
        'class="action-btn action-btn-info flex-1"'
    ),
    # Start button (green success - originally bg-rack-primary)
    (
        r'class="flex flex-1 items-center justify-center gap-2 rounded-lg bg-rack-primary px-3 py-2 text-sm text-white transition-colors hover:bg-rack-primary/90 disabled:opacity-50"',
        'class="action-btn action-btn-success flex-1"'
    ),
    # Retry button (yellow warning)
    (
        r'class="flex flex-1 items-center justify-center gap-2 rounded-lg bg-yellow-500/20 px-3 py-2 text-sm text-yellow-400 transition-colors hover:bg-yellow-500/30 disabled:opacity-50"',
        'class="action-btn action-btn-warning flex-1"'
    ),
    # Delete button (red danger)
    (
        r'class="flex items-center justify-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400 transition-colors hover:bg-red-500/20 disabled:opacity-50"',
        'class="action-btn action-btn-danger"'
    ),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# Also wrap button text in <span> tags
# Replace button text patterns
text_replacements = [
    (r'(\s+)(View Logs)(\s+</button>)', r'\1<span>\2</span>\3'),
    (r'(\s+)(Stop)(\s+</button>)', r'\1<span>\2</span>\3'),
    (r'(\s+)(Restart)(\s+</button>)', r'\1<span>\2</span>\3'),
    (r'(\s+)(Clone)(\s+</button>)', r'\1<span>\2</span>\3'),
    (r'(\s+)(Start)(\s+</button>)', r'\1<span>\2</span>\3'),
    (r'(\s+)(Retry)(\s+</button>)', r'\1<span>\2</span>\3'),
]

for pattern, replacement in text_replacements:
    content = re.sub(pattern, replacement, content)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print(f"✅ Updated {file_path}")
print("Applied replacements:")
print("- Stop button → action-btn-warning")
print("- Restart button → action-btn-primary")
print("- Clone button → action-btn-info")
print("- Start button → action-btn-success")
print("- Retry button → action-btn-warning")
print("- Delete button → action-btn-danger")
print("- Wrapped button text in <span> tags")
