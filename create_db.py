import sqlite3

conn = sqlite3.connect('students.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS students')  # Clear old table

cursor.execute('''
    CREATE TABLE students(
        roll TEXT,
        name TEXT,
        position TEXT,
        subj1 INTEGER,
        subj2 INTEGER
    )
''')
students = [
    ('101', 'Noman', '1st', 85, 90),
    ('102', 'Naqi Anjum', '2nd', 78, 80),
    ('103', 'Mubarak', '3rd', 82, 85),
    ('104', 'Tasawwur', '4th', 75, 70),
    ('105', 'Hasan', '5th', 81, 82),
    ('786', 'Afsana Mondal', '1st', 88, 87),
    ('787', 'Aqifa Fatima', '2nd', 65, 47),
]



cursor.executemany('INSERT INTO students VALUES (?, ?, ?, ?, ?)', students)
conn.commit()
conn.close()
