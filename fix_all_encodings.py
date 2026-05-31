"""
Fix encoding issues in all loader scripts
Removes emoji and unicode chars that cause cp1252 errors on Windows
"""
import os
import re

scripts_dir = 'scripts'
os.makedirs(scripts_dir, exist_ok=True)

# Emoji patterns to remove
emoji_pattern = re.compile("["
    u"\U0001F600-\U0001F64F"  # emoticons
    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
    u"\U0001F680-\U0001F6FF"  # transport & map symbols
    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    u"\U0001f900-\U0001f9ff"
    "]+", flags=re.UNICODE)

# Common replacements
replacements = {
    '\U0001f680': '[>]',  # rocket -> arrow
    '\U0001f504': '[SYNC]',  # sync
    '\U0001f4e6': '[OUT]',  # package
    '\U0001f4ca': '[STAT]',  # chart
    '\U0001f4c8': '[GRAPH]',  # chart
    '\U0001f440': '[OK]',  # eyes
    '\U00002705': '[OK]',  # check mark
    '\U0000274c': '[X]',  # cross
    '\U0001f49a': '[OK]',  # yellow heart
    '\U0001f504': '[ROT]',  # rotating
    '\U0001f501': '[LOOP]',  # loop
}

def fix_file(filepath):
    """Fix encoding issues in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Remove all emojis
        content = emoji_pattern.sub('', content)

        # Fix specific unicode chars
        for char, replacement in replacements.items():
            content = content.replace(char, replacement)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

# Fix all Python scripts in scripts directory
print("Fixing encoding in all scripts...")
fixed_count = 0

for filename in os.listdir(scripts_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(scripts_dir, filename)
        if fix_file(filepath):
            print(f"  Fixed: {filename}")
            fixed_count += 1

print(f"\nTotal fixed: {fixed_count} files")
print("You can now run the scripts without encoding errors!")