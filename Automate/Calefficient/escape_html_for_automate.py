import sys
import os
import pyperclip

def escape_text(input_file):
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    # Get file name and extension
    file_name, file_ext = os.path.splitext(input_file)
    output_file = f"{file_name}_escaped{file_ext}"

    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split content into lines
        lines = content.split('\n')
        processed_lines = []
        skip_next = False

        for line in lines:
            if skip_next:
                skip_next = False
                continue

            line = line.lstrip(' \t').strip()

            if line.startswith('//not automate'):
                skip_next = True
                continue

            if line.startswith('//automate'):
                # For automate lines, remove the prefix and strip all whitespace including tabs
                processed_line = line.replace('//automate', '')
                print(processed_line)
                processed_lines.append(processed_line)
            else:
                # For other lines, apply all escapes
                processed_line = line.replace('{', '\\{')
                processed_line = processed_line.replace('"', '\\"')
                processed_lines.append(processed_line)

        # Join lines with escaped newlines
        escaped_content = '\\n'.join(processed_lines)

        # Add quotes at the beginning and end
        escaped_content = f'"{escaped_content}"'

        # Write to output file
        # with open(output_file, 'w', encoding='utf-8') as f:
        #     f.write(escaped_content)

        # Copy to clipboard
        pyperclip.copy(escaped_content)

        print(f"Successfully processed file: {input_file}")
        print("Content has been copied to clipboard")

    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        input_file = "web_dialog.html"
        # print("Usage: python escape_text.py <input_file>")
        # sys.exit(1)
    else:
        input_file = sys.argv[1]

    escape_text(input_file) 