#!/usr/bin/env python3
"""
Script to convert action buttons to icon-only format (matching flip button)
"""

import re

file_path = "frontend/src/routes/apps/+page.svelte"

with open(file_path, 'r') as f:
    content = f.read()

# Remove flex-1 class from all action buttons
content = re.sub(r'class="action-btn (action-btn-\w+) flex-1"', r'class="action-btn \1"', content)

# Remove <span> text labels from buttons (but keep the icon)
# Pattern: icon + span with text + closing button tag
patterns_to_fix = [
    # Stop button
    (r'(<StopCircle class="h-4 w-4" />)\s*{/if}\s*<span>Stop</span>', r'\1\n\t\t\t\t\t\t\t\t{/if}'),
    # Restart button
    (r'(<RotateCw class="h-4 w-4" />)\s*{/if}\s*<span>Restart</span>', r'\1\n\t\t\t\t\t\t\t\t{/if}'),
    # Clone button (no conditional)
    (r'(<Copy class="h-4 w-4" />)\s*<span>Clone</span>', r'\1'),
    # Start button  
    (r'(<PlayCircle class="h-4 w-4" />)\s*{/if}\s*<span>Start</span>', r'\1\n\t\t\t\t\t\t\t\t{/if}'),
    # Retry button
    (r'(<RotateCw class="h-4 w-4" />)\s*{/if}\s*<span>Retry</span>', r'\1\n\t\t\t\t\t\t\t\t{/if}'),
]

for pattern, replacement in patterns_to_fix:
    content = re.sub(pattern, replacement, content)

# Add title attributes for accessibility
# Stop button
content = re.sub(
    r'(on:click=\{\(\) => handleAction\(app\.id, app\.name, \'stop\'\)\})\s*(disabled=\{actionInProgress\[app\.id\]\})\s*(class="action-btn action-btn-warning")',
    r'\1\n\t\t\t\t\t\t\t\t\2\n\t\t\t\t\t\t\t\t\3\n\t\t\t\t\t\t\t\ttitle="Stop"',
    content
)

# Restart button
content = re.sub(
    r'(on:click=\{\(\) => handleAction\(app\.id, app\.name, \'restart\'\)\})\s*(disabled=\{actionInProgress\[app\.id\]\})\s*(class="action-btn action-btn-primary")',
    r'\1\n\t\t\t\t\t\t\t\t\2\n\t\t\t\t\t\t\t\t\3\n\t\t\t\t\t\t\t\ttitle="Restart"',
    content
)

# Clone button
content = re.sub(
    r'(data-testid="clone-button")\s*(on:click=\{\(\) => handleClone\(app\)\})\s*(disabled=\{actionInProgress\[app\.id\]\})\s*(class="action-btn action-btn-info")',
    r'\1\n\t\t\t\t\t\t\t\t\2\n\t\t\t\t\t\t\t\t\3\n\t\t\t\t\t\t\t\t\4\n\t\t\t\t\t\t\t\ttitle="Clone"',
    content
)

# Start button
content = re.sub(
    r'(on:click=\{\(\) => handleAction\(app\.id, app\.name, \'start\'\)\})\s*(disabled=\{actionInProgress\[app\.id\]\})\s*(class="action-btn action-btn-success")',
    r'\1\n\t\t\t\t\t\t\t\t\2\n\t\t\t\t\t\t\t\t\3\n\t\t\t\t\t\t\t\ttitle="Start"',
    content
)

# Delete button
content = re.sub(
    r'(disabled=\{actionInProgress\[app\.id\]\})\s*(class="action-btn action-btn-danger">)',
    r'\1\n\t\t\t\t\t\t\t\t\2',
    content
)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print(f"✅ Updated {file_path}")
print("Applied changes:")
print("- Removed flex-1 from all action buttons")
print("- Removed text labels (<span> tags)")
print("- Added title attributes for tooltips")
print("- Buttons now match flip button style (icon-only, 32px square)")
