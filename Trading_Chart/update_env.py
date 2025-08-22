"""Update .env file to use SQL authentication."""

import os

# Read current .env file
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update the trusted connection setting
    updated_lines = []
    for line in lines:
        if line.startswith('DB_TRUSTED_CONNECTION='):
            updated_lines.append('DB_TRUSTED_CONNECTION=no\n')
        else:
            updated_lines.append(line)
    
    # Write back to .env
    with open('.env', 'w') as f:
        f.writelines(updated_lines)
    
    print("Updated .env file: DB_TRUSTED_CONNECTION=no")
else:
    print(".env file not found")