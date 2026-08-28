-- EXAMORA Database Schema Definition
-- Database: online_examination

-- 1. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Administrators Table
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Questions Bank Table with Subject/Category Support
CREATE TABLE IF NOT EXISTS questions (
    qid INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) DEFAULT 'Computer Science & IT',
    question VARCHAR(255) NOT NULL,
    optionA VARCHAR(150) NOT NULL,
    optionB VARCHAR(150) NOT NULL,
    optionC VARCHAR(150) NOT NULL,
    optionD VARCHAR(150) NOT NULL,
    correct_answer CHAR(1) NOT NULL,
    marks INT DEFAULT 1
) ENGINE=InnoDB;

-- 4. Student Exam Sessions Table (Server-Authoritative Timer & State)
CREATE TABLE IF NOT EXISTS student_exam_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL UNIQUE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT NOT NULL DEFAULT 3600,
    status VARCHAR(16) DEFAULT 'active',
    submitted_at TIMESTAMP NULL
) ENGINE=InnoDB;

-- 5. Student Results Summary Table
CREATE TABLE IF NOT EXISTS student_results (
    student_id INT UNIQUE,
    student_name VARCHAR(100),
    score INT NOT NULL DEFAULT 0,
    total_marks INT NOT NULL DEFAULT 0,
    percentage FLOAT NOT NULL DEFAULT 0.0,
    grade VARCHAR(8) NOT NULL DEFAULT 'F',
    exam_date DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 6. Student Answer Submissions Table
CREATE TABLE IF NOT EXISTS student_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    qid INT NOT NULL,
    selected_answer VARCHAR(16),
    correct_answer VARCHAR(16),
    marks INT DEFAULT 0,
    marks_obtained INT DEFAULT 0,
    exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student_qid (student_id, qid)
) ENGINE=InnoDB;

-- 7. Student Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'system',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student_unread (student_id, is_read)
) ENGINE=InnoDB;
