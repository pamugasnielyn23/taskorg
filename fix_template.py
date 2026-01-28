import os

path = r'c:\Users\User\taskorg\organizer\templates\organizer\task_form.html'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if '{% if' in line and 'subtask.is_completed' in lines[i+1] and 'checked' in lines[i+1]:
        # Join lines i and i+1
        joined = line.strip() + ' ' + lines[i+1].strip() + '\n'
        new_lines.append(joined)
        i += 2
    else:
        new_lines.append(line)
        i += 1

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("SUCCESS: Joined lines in task_form.html")
