def check_and_append_line(file_path, line_to_add):
    try:
        # Read the content of the file
        with open(file_path, 'r') as file:
            content = file.readlines()

        # Check if the line is already present in the file
        if line_to_add + '\n' not in content:
            # Append the line to the file if it's not present
            with open(file_path, 'a') as file:
                file.write(line_to_add + '\n')
            print(f"Line '{line_to_add}' appended to {file_path}.")
        else:
            print(f"Line '{line_to_add}' is already present in {file_path}.")
    except Exception as e:
        print(f"Error: {e}")

# Define the file path and the line to check and append
file_path = '/boot/firmware/config.txt'
line_to_add = 'dtoverlay=spi0-0cs'

# Run the function to check and append the line
check_and_append_line(file_path, line_to_add)

