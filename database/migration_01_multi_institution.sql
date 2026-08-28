CREATE TABLE IF NOT EXISTS institutions (
    institution_id INT AUTO_INCREMENT PRIMARY KEY,
    institution_name VARCHAR(150) NOT NULL,
    logo VARCHAR(255),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO institutions (institution_id, institution_name, email, status) 
VALUES (1, 'Default Institution', 'admin@examora.com', 'active')
ON DUPLICATE KEY UPDATE institution_name='Default Institution';

-- ADMINS
ALTER TABLE admins 
ADD COLUMN institution_id INT DEFAULT NULL,
ADD COLUMN role VARCHAR(50) DEFAULT 'SUPER_ADMIN';

ALTER TABLE admins
ADD CONSTRAINT fk_admins_institution FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE;

-- Default existing admin to SUPER_ADMIN (no institution_id needed, or maybe default to 1?)
-- Wait, Super Admin is global. They don't have an institution_id.

-- STUDENTS
ALTER TABLE students 
ADD COLUMN institution_id INT DEFAULT 1;

ALTER TABLE students
ADD CONSTRAINT fk_students_institution FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE;

-- EXAMINATIONS
ALTER TABLE examinations 
ADD COLUMN institution_id INT DEFAULT 1;

ALTER TABLE examinations
ADD CONSTRAINT fk_examinations_institution FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE;

-- QUESTIONS
ALTER TABLE questions 
ADD COLUMN institution_id INT DEFAULT 1;

ALTER TABLE questions
ADD CONSTRAINT fk_questions_institution FOREIGN KEY (institution_id) REFERENCES institutions(institution_id) ON DELETE CASCADE;
