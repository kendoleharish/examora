ALTER TABLE student_answers
ADD COLUMN answer_text TEXT,
ADD COLUMN answer_json JSON,
ADD COLUMN evaluation_status VARCHAR(20) DEFAULT 'AUTO_SCORED',
ADD COLUMN evaluator_id INT DEFAULT NULL,
ADD COLUMN feedback TEXT,
ADD COLUMN ai_score FLOAT DEFAULT NULL,
ADD COLUMN ai_reasoning TEXT;

ALTER TABLE student_results
MODIFY COLUMN status VARCHAR(20) DEFAULT 'PASSED';
-- Oh wait, student_results doesn't have a status column. Let me check the schema.
-- It has grade (varchar 8), percentage, score.
-- Let's add status to student_results.
ALTER TABLE student_results
ADD COLUMN status VARCHAR(20) DEFAULT 'FINAL';

-- Update foreign key on evaluator_id to admins
ALTER TABLE student_answers
ADD CONSTRAINT fk_student_answers_evaluator FOREIGN KEY (evaluator_id) REFERENCES admins(admin_id) ON DELETE SET NULL;
