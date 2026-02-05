
import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

# Create organizer_subtask table if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS organizer_subtask (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200) NOT NULL,
        is_completed INTEGER DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        task_id INTEGER NOT NULL,
        FOREIGN KEY (task_id) REFERENCES organizer_task(id) ON DELETE CASCADE
    )
''')
print("Created organizer_subtask table")

conn.commit()
conn.close()
print("Done!")
