CREATE TABLE IF NOT EXISTS exam_sections (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    time_limit_minutes INT DEFAULT NULL,
    marks_per_question INT DEFAULT NULL,
    negative_marks_per_question INT DEFAULT NULL,
    randomize_order BOOLEAN DEFAULT FALSE,
    order_index INT DEFAULT 0,
    FOREIGN KEY (exam_id) REFERENCES examinations(exam_id) ON DELETE CASCADE
);

ALTER TABLE exam_questions
ADD COLUMN section_id INT DEFAULT NULL,
ADD COLUMN order_index INT DEFAULT 0;

ALTER TABLE exam_questions
ADD CONSTRAINT fk_exam_questions_section FOREIGN KEY (section_id) REFERENCES exam_sections(section_id) ON DELETE CASCADE;
