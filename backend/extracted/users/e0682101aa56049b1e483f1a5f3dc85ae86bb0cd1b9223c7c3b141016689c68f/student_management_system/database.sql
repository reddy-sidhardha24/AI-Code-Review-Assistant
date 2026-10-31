CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    age TEXT
);

INSERT INTO students (name, email, age)
VALUES ('Ravi', 'ravi@example.com', '20');

INSERT INTO students (name, email, age)
VALUES ('Ravi Kumar', 'ravi@example.com', '21');

INSERT INTO students (name, email, age)
VALUES ('Test User', 'test@example.com', '-5');

SELECT * FROM students
WHERE name LIKE '%Ravi%';

SELECT * FROM students
WHERE email = 'ravi@example.com';

DELETE FROM students;