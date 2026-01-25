#!/usr/bin/env python3
"""Fix indentation in app.py display_image function"""

with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the display_image function try block (lines 494-521)
# Line numbers are 0-indexed, so line 494 is index 493

# Line 494: if self.placeholder: -> needs 12 spaces
if 493 < len(lines):
    lines[493] = '            if self.placeholder:\n'

# Line 495: self.placeholder.place_forget() -> needs 16 spaces  
if 494 < len(lines):
    lines[494] = '                self.placeholder.place_forget()\n'

# Line 496: if hasattr -> needs 12 spaces
if 495 < len(lines):
    lines[495] = '            if hasattr(self, \'placeholder_icon\'):\n'

# Line 497: self.placeholder_icon.place_forget() -> needs 16 spaces
if 496 < len(lines):
    lines[496] = '                self.placeholder_icon.place_forget()\n'

# Lines 499-521: all need 12 spaces (except nested if blocks which need 16)
for i in range(498, 521):
    if i < len(lines):
        line = lines[i].rstrip()
        stripped = line.lstrip()
        
        if not stripped or stripped.startswith('except'):
            continue
            
        # Check if it's inside an if block (after line 515)
        if i >= 515 and ('self.image_label =' in stripped or 'self.image_label.place' in stripped):
            # Inside if block - needs 16 spaces
            lines[i] = '                ' + stripped + '\n'
        elif 'return' in stripped and i == 503:
            # Inside if block - needs 16 spaces
            lines[i] = '                ' + stripped + '\n'
        else:
            # Regular try block content - needs 12 spaces
            lines[i] = '            ' + stripped + '\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed indentation in display_image function")



