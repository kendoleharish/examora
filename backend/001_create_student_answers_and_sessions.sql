-- Migration: create student_answers and student_exam_sessions tables

CREATE TABLE IF NOT EXISTS student_answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    qid INT NOT NULL,
    selected_answer VARCHAR(16),
    correct_answer VARCHAR(16),
    marks INT DEFAULT 0,
    marks_obtained INT DEFAULT 0,
    exam_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (student_id),
    INDEX (qid)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS student_exam_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL UNIQUE,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT NOT NULL,
    INDEX (student_id)
) ENGINE=InnoDB;
