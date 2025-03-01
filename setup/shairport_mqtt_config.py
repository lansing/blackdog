
import sys
import shutil
import re

# Define the markers
START_MARKER = "// BEGIN blackdog-shairport mqtt config"
END_MARKER = "// END blackdog-shairport mqtt config"

# Function to identify settings from a mods file
def extract_settings(mods_file):
    settings = []
    pattern = r"^(\w+)\s*=\s*{[\s\S]*?}"
    
    with open(mods_file, 'r') as file:
        lines = file.read()
        settings = re.findall(pattern, lines, flags=re.MULTILINE)
    
    return settings

# Function to comment out entire settings in the target file
def comment_out_settings(target_content, settings):
    inside_modifications = False
    new_content = []
    commented_settings = set()

    i = 0
    while i < len(target_content):
        line = target_content[i].strip()
        
        # Check if the line matches a setting declaration and isn't already commented out
        for setting in settings:
            # Match a setting key (ignoring whitespace) and possibly opening bracket on next line
            if line.startswith(f"{setting} =") and setting not in commented_settings:
                # Start commenting out this setting
                new_content.append(f"\n// Commenting out {setting} on behalf of blackdog-shairport\n")
                # Continue to comment out the lines until we find the closing `};`
                while not line.endswith("};") and i < len(target_content):
                    new_content.append(f"// {target_content[i].strip()}\n")
                    i += 1
                    line = target_content[i].strip()
                # Comment out the line with the closing bracket `};`
                new_content.append(f"// {target_content[i].strip()}\n")
                commented_settings.add(setting)
                break
        else:
            # If no setting matched, just add the line as is
            new_content.append(target_content[i])

        i += 1
    
    return new_content

def modify_conf_file(target_file, mods_file):
    # Backup the target file
    shutil.copy(target_file, f"{target_file}.bak")
    print(f"Backup of {target_file} created as {target_file}.bak")

    # Extract the settings from the mods file
    settings_to_modify = extract_settings(mods_file)
    print(f"Settings to modify: {settings_to_modify}")

    # Read the target file content
    with open(target_file, 'r') as file:
        target_content = file.readlines()

    # Comment out the existing settings if they exist
    target_content = comment_out_settings(target_content, settings_to_modify)

    # Remove any existing modifications between the markers
    inside_modifications = False
    clean_content = []
    for line in target_content:
        if START_MARKER in line:
            inside_modifications = True
        elif END_MARKER in line:
            inside_modifications = False
        if not inside_modifications:
            clean_content.append(line)

    # Read the mods file content
    with open(mods_file, 'r') as file:
        mods_content = file.read()

    # Insert the new content between the markers
    clean_content.append(f"\n{START_MARKER}\n")
    clean_content.append(mods_content)
    clean_content.append(f"\n{END_MARKER}\n")

    # Write the modified content back to the target file
    with open(target_file, 'w') as file:
        file.writelines(clean_content)

    print(f"Modifications applied to {target_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python modify_conf.py <target_file> <mods_file>")
        sys.exit(1)

    target_file = sys.argv[1]
    mods_file = sys.argv[2]

    modify_conf_file(target_file, mods_file)
