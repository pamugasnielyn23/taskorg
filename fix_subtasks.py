import os

path = r'c:\Users\User\taskorg\organizer\templates\organizer\task_form.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = []
skip_next = False
for i in range(len(lines)):
    if skip_next:
        skip_next = False
        continue
    
    line = lines[i]
    if '{% if' in line and i + 1 < len(lines) and 'subtask.is_completed %}checked{% endif %}' in lines[i+1]:
        # Join this line with the next
        joined = line.rstrip() + ' ' + lines[i+1].lstrip()
        output_lines.append(joined)
        skip_next = True
        print(f"DEBUG: Joined lines {i+1} and {i+2}")
    else:
        output_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(output_lines)
print("SUCCESS: Full repair completed.")
