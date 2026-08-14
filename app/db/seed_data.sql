-- Seed data for mock database
-- Centers
INSERT INTO Center (id, name, city, state, is_active) VALUES
(1, 'Center Delhi', 'Delhi', 'Delhi', 1),
(2, 'Center Mumbai', 'Mumbai', 'Maharashtra', 1);

-- Batches
INSERT INTO Batch (id, name, center_id, start_date, end_date, is_active) VALUES
(1, 'Batch A', 1, '2024-01-15', '2024-12-15', 1),
(2, 'Batch B', 1, '2024-03-01', '2025-02-28', 1),
(3, 'Batch C', 2, '2024-02-01', '2025-01-31', 1);

-- Students (25 students across centers)
INSERT INTO Student (id, name, email, phone, batch_id, center_id, enrollment_date, is_active) VALUES
(1, 'Aarav Sharma', 'aarav@college.edu', '9876543001', 1, 1, '2024-01-15', 1),
(2, 'Priya Patel', 'priya@college.edu', '9876543002', 1, 1, '2024-01-15', 1),
(3, 'Rahul Kumar', 'rahul@college.edu', '9876543003', 1, 1, '2024-01-15', 1),
(4, 'Sneha Gupta', 'sneha@college.edu', '9876543004', 1, 1, '2024-01-15', 1),
(5, 'Vikram Singh', 'vikram@college.edu', '9876543005', 1, 1, '2024-01-15', 1),
(6, 'Ananya Reddy', 'ananya@college.edu', '9876543006', 2, 1, '2024-03-01', 1),
(7, 'Karan Mehta', 'karan@college.edu', '9876543007', 2, 1, '2024-03-01', 1),
(8, 'Divya Joshi', 'divya@college.edu', '9876543008', 2, 1, '2024-03-01', 1),
(9, 'Arjun Nair', 'arjun@college.edu', '9876543009', 2, 1, '2024-03-01', 1),
(10, 'Meera Iyer', 'meera@college.edu', '9876543010', 2, 1, '2024-03-01', 1),
(11, 'Rohan Das', 'rohan@college.edu', '9876543011', 3, 2, '2024-02-01', 1),
(12, 'Pooja Verma', 'pooja@college.edu', '9876543012', 3, 2, '2024-02-01', 1),
(13, 'Amit Yadav', 'amit@college.edu', '9876543013', 3, 2, '2024-02-01', 1),
(14, 'Neha Agarwal', 'neha@college.edu', '9876543014', 3, 2, '2024-02-01', 1),
(15, 'Siddharth Roy', 'siddharth@college.edu', '9876543015', 3, 2, '2024-02-01', 1),
(16, 'Kavya Menon', 'kavya@college.edu', '9876543016', 3, 2, '2024-02-01', 1),
(17, 'Harsh Pandey', 'harsh@college.edu', '9876543017', 1, 1, '2024-01-15', 1),
(18, 'Riya Saxena', 'riya@college.edu', '9876543018', 1, 1, '2024-01-15', 1),
(19, 'Deepak Mishra', 'deepak@college.edu', '9876543019', 2, 1, '2024-03-01', 1),
(20, 'Tanvi Chauhan', 'tanvi@college.edu', '9876543020', 2, 1, '2024-03-01', 1),
(21, 'Nikhil Bhatt', 'nikhil@college.edu', '9876543021', 3, 2, '2024-02-01', 1),
(22, 'Shruti Kapoor', 'shruti@college.edu', '9876543022', 3, 2, '2024-02-01', 1),
(23, 'Aditya Tiwari', 'aditya@college.edu', '9876543023', 1, 1, '2024-01-15', 1),
(24, 'Ishita Bose', 'ishita@college.edu', '9876543024', 2, 1, '2024-03-01', 1),
(25, 'Manish Dubey', 'manish@college.edu', '9876543025', 3, 2, '2024-02-01', 1);

-- Subjects
INSERT INTO Subject (id, name, code, description) VALUES
(1, 'Mathematics', 'MATH101', 'Fundamental mathematics'),
(2, 'Data Structures', 'CS201', 'Data structures and algorithms'),
(3, 'Web Development', 'CS301', 'Full stack web development'),
(4, 'Database Systems', 'CS401', 'Database design and SQL'),
(5, 'Machine Learning', 'CS501', 'Introduction to ML');

-- Classes (2 weeks of classes: Week 1 = Jan 15-19, Week 2 = Jan 22-26)
INSERT INTO Class (id, subject_id, batch_id, center_id, instructor_name, class_date, start_time, end_time) VALUES
(1, 1, 1, 1, 'Prof. Sharma', '2024-01-15', '09:00', '10:30'),
(2, 2, 1, 1, 'Prof. Verma', '2024-01-16', '09:00', '10:30'),
(3, 3, 1, 1, 'Prof. Gupta', '2024-01-17', '09:00', '10:30'),
(4, 4, 1, 1, 'Prof. Kumar', '2024-01-18', '09:00', '10:30'),
(5, 5, 1, 1, 'Prof. Iyer', '2024-01-19', '09:00', '10:30'),
(6, 1, 1, 1, 'Prof. Sharma', '2024-01-22', '09:00', '10:30'),
(7, 2, 1, 1, 'Prof. Verma', '2024-01-23', '09:00', '10:30'),
(8, 3, 1, 1, 'Prof. Gupta', '2024-01-24', '09:00', '10:30'),
(9, 4, 1, 1, 'Prof. Kumar', '2024-01-25', '09:00', '10:30'),
(10, 5, 1, 1, 'Prof. Iyer', '2024-01-26', '09:00', '10:30'),
(11, 1, 3, 2, 'Prof. Reddy', '2024-01-15', '10:00', '11:30'),
(12, 2, 3, 2, 'Prof. Reddy', '2024-01-16', '10:00', '11:30'),
(13, 3, 3, 2, 'Prof. Das', '2024-01-17', '10:00', '11:30'),
(14, 4, 3, 2, 'Prof. Das', '2024-01-18', '10:00', '11:30'),
(15, 5, 3, 2, 'Prof. Nair', '2024-01-19', '10:00', '11:30'),
(16, 1, 3, 2, 'Prof. Reddy', '2024-01-22', '10:00', '11:30'),
(17, 2, 3, 2, 'Prof. Reddy', '2024-01-23', '10:00', '11:30'),
(18, 3, 3, 2, 'Prof. Das', '2024-01-24', '10:00', '11:30'),
(19, 4, 3, 2, 'Prof. Das', '2024-01-25', '10:00', '11:30'),
(20, 5, 3, 2, 'Prof. Nair', '2024-01-26', '10:00', '11:30');

-- Attendance for Week 1 (Center 1, Batch A students 1-5)
-- Student 1 (Aarav): 100% week1, will be 60% week2 (attendance DROP)
INSERT INTO Attendance (student_id, class_id, center_id, attendance_date, status) VALUES
(1, 1, 1, '2024-01-15', 'present'),
(1, 2, 1, '2024-01-16', 'present'),
(1, 3, 1, '2024-01-17', 'present'),
(1, 4, 1, '2024-01-18', 'present'),
(1, 5, 1, '2024-01-19', 'present'),
-- Student 2 (Priya): 40% week1, will be 80% week2 (attendance RISE of 40%)
(2, 1, 1, '2024-01-15', 'present'),
(2, 2, 1, '2024-01-16', 'absent'),
(2, 3, 1, '2024-01-17', 'present'),
(2, 4, 1, '2024-01-18', 'absent'),
(2, 5, 1, '2024-01-19', 'absent'),
-- Student 3 (Rahul): 60% week1, will be 100% week2 (attendance RISE of 40%)
(3, 1, 1, '2024-01-15', 'present'),
(3, 2, 1, '2024-01-16', 'present'),
(3, 3, 1, '2024-01-17', 'present'),
(3, 4, 1, '2024-01-18', 'absent'),
(3, 5, 1, '2024-01-19', 'absent'),
-- Student 4 (Sneha): 80% week1, will be 80% week2 (no change)
(4, 1, 1, '2024-01-15', 'present'),
(4, 2, 1, '2024-01-16', 'present'),
(4, 3, 1, '2024-01-17', 'present'),
(4, 4, 1, '2024-01-18', 'present'),
(4, 5, 1, '2024-01-19', 'absent'),
-- Student 5 (Vikram): 20% week1, will be 60% week2 (attendance RISE of 40%)
(5, 1, 1, '2024-01-15', 'absent'),
(5, 2, 1, '2024-01-16', 'absent'),
(5, 3, 1, '2024-01-17', 'absent'),
(5, 4, 1, '2024-01-18', 'present'),
(5, 5, 1, '2024-01-19', 'absent');

-- Attendance for Week 2 (Center 1, Batch A students 1-5)
INSERT INTO Attendance (student_id, class_id, center_id, attendance_date, status) VALUES
-- Student 1 (Aarav): 60% week2 (drop from 100%)
(1, 6, 1, '2024-01-22', 'present'),
(1, 7, 1, '2024-01-23', 'present'),
(1, 8, 1, '2024-01-24', 'absent'),
(1, 9, 1, '2024-01-25', 'present'),
(1, 10, 1, '2024-01-26', 'absent'),
-- Student 2 (Priya): 80% week2 (rise from 40%)
(2, 6, 1, '2024-01-22', 'present'),
(2, 7, 1, '2024-01-23', 'present'),
(2, 8, 1, '2024-01-24', 'present'),
(2, 9, 1, '2024-01-25', 'present'),
(2, 10, 1, '2024-01-26', 'absent'),
-- Student 3 (Rahul): 100% week2 (rise from 60%)
(3, 6, 1, '2024-01-22', 'present'),
(3, 7, 1, '2024-01-23', 'present'),
(3, 8, 1, '2024-01-24', 'present'),
(3, 9, 1, '2024-01-25', 'present'),
(3, 10, 1, '2024-01-26', 'present'),
-- Student 4 (Sneha): 80% week2 (no change)
(4, 6, 1, '2024-01-22', 'present'),
(4, 7, 1, '2024-01-23', 'present'),
(4, 8, 1, '2024-01-24', 'absent'),
(4, 9, 1, '2024-01-25', 'present'),
(4, 10, 1, '2024-01-26', 'present'),
-- Student 5 (Vikram): 60% week2 (rise from 20%)
(5, 6, 1, '2024-01-22', 'present'),
(5, 7, 1, '2024-01-23', 'present'),
(5, 8, 1, '2024-01-24', 'present'),
(5, 9, 1, '2024-01-25', 'absent'),
(5, 10, 1, '2024-01-26', 'absent');

-- Attendance for Center 2 students (Week 1 and Week 2)
INSERT INTO Attendance (student_id, class_id, center_id, attendance_date, status) VALUES
(11, 11, 2, '2024-01-15', 'present'),
(11, 12, 2, '2024-01-16', 'present'),
(11, 13, 2, '2024-01-17', 'present'),
(11, 14, 2, '2024-01-18', 'present'),
(11, 15, 2, '2024-01-19', 'present'),
(12, 11, 2, '2024-01-15', 'present'),
(12, 12, 2, '2024-01-16', 'absent'),
(12, 13, 2, '2024-01-17', 'present'),
(12, 14, 2, '2024-01-18', 'present'),
(12, 15, 2, '2024-01-19', 'present'),
(13, 11, 2, '2024-01-15', 'absent'),
(13, 12, 2, '2024-01-16', 'absent'),
(13, 13, 2, '2024-01-17', 'present'),
(13, 14, 2, '2024-01-18', 'absent'),
(13, 15, 2, '2024-01-19', 'absent'),
(11, 16, 2, '2024-01-22', 'present'),
(11, 17, 2, '2024-01-23', 'present'),
(11, 18, 2, '2024-01-24', 'present'),
(11, 19, 2, '2024-01-25', 'present'),
(11, 20, 2, '2024-01-26', 'present'),
(12, 16, 2, '2024-01-22', 'present'),
(12, 17, 2, '2024-01-23', 'present'),
(12, 18, 2, '2024-01-24', 'present'),
(12, 19, 2, '2024-01-25', 'present'),
(12, 20, 2, '2024-01-26', 'present'),
(13, 16, 2, '2024-01-22', 'present'),
(13, 17, 2, '2024-01-23', 'present'),
(13, 18, 2, '2024-01-24', 'present'),
(13, 19, 2, '2024-01-25', 'absent'),
(13, 20, 2, '2024-01-26', 'present');

-- Exams
INSERT INTO Exam (id, name, subject_id, batch_id, exam_date, total_marks) VALUES
(1, 'Math Mid-Term', 1, 1, '2024-02-15', 100),
(2, 'DS Mid-Term', 2, 1, '2024-02-16', 100),
(3, 'Math Mid-Term', 1, 3, '2024-02-17', 100),
(4, 'Web Dev Practical', 3, 1, '2024-03-01', 50);

-- Student Exam Marks
INSERT INTO StudentExamMarks (student_id, exam_id, marks_obtained, grade) VALUES
(1, 1, 92, 'A+'),
(2, 1, 78, 'B+'),
(3, 1, 65, 'B'),
(4, 1, 88, 'A'),
(5, 1, 45, 'C'),
(1, 2, 85, 'A'),
(2, 2, 90, 'A+'),
(3, 2, 72, 'B+'),
(4, 2, 68, 'B'),
(5, 2, 55, 'C+'),
(11, 3, 95, 'A+'),
(12, 3, 82, 'A'),
(13, 3, 60, 'B'),
(14, 3, 75, 'B+'),
(15, 3, 88, 'A'),
(1, 4, 45, 'A'),
(2, 4, 40, 'A'),
(3, 4, 35, 'B+'),
(4, 4, 42, 'A'),
(5, 4, 28, 'C');

-- Problems (Coding platform)
INSERT INTO Problem (id, title, difficulty, topic, points) VALUES
(1, 'Two Sum', 'easy', 'Arrays', 10),
(2, 'Reverse Linked List', 'easy', 'Linked Lists', 10),
(3, 'Binary Search', 'easy', 'Searching', 10),
(4, 'LRU Cache', 'medium', 'Design', 20),
(5, 'Merge Intervals', 'medium', 'Arrays', 20),
(6, 'Word Break', 'medium', 'Dynamic Programming', 20),
(7, 'Median of Two Sorted Arrays', 'hard', 'Arrays', 30),
(8, 'Regular Expression Matching', 'hard', 'Strings', 30);

-- Submissions
INSERT INTO Submission (student_id, problem_id, submitted_at, status, language) VALUES
(1, 1, '2024-01-20 10:00:00', 'accepted', 'Python'),
(1, 2, '2024-01-20 11:00:00', 'accepted', 'Python'),
(1, 3, '2024-01-21 09:00:00', 'accepted', 'Python'),
(1, 4, '2024-01-22 14:00:00', 'accepted', 'Python'),
(1, 5, '2024-01-23 10:00:00', 'wrong_answer', 'Python'),
(2, 1, '2024-01-20 10:30:00', 'accepted', 'Java'),
(2, 2, '2024-01-21 11:00:00', 'accepted', 'Java'),
(2, 4, '2024-01-22 15:00:00', 'time_limit', 'Java'),
(3, 1, '2024-01-20 12:00:00', 'accepted', 'C++'),
(3, 2, '2024-01-21 12:00:00', 'wrong_answer', 'C++'),
(3, 3, '2024-01-22 09:00:00', 'accepted', 'C++'),
(11, 1, '2024-01-20 10:00:00', 'accepted', 'Python'),
(11, 2, '2024-01-20 11:00:00', 'accepted', 'Python'),
(11, 3, '2024-01-21 09:00:00', 'accepted', 'Python'),
(11, 4, '2024-01-22 14:00:00', 'accepted', 'Python'),
(11, 5, '2024-01-23 10:00:00', 'accepted', 'Python'),
(11, 6, '2024-01-24 10:00:00', 'accepted', 'Python'),
(11, 7, '2024-02-01 10:00:00', 'accepted', 'Python'),
(12, 1, '2024-01-20 10:30:00', 'accepted', 'JavaScript'),
(12, 2, '2024-01-21 11:00:00', 'accepted', 'JavaScript');

-- Contests
INSERT INTO Contest (id, name, contest_date, duration_minutes) VALUES
(1, 'Weekly Contest 1', '2024-01-21', 120),
(2, 'Weekly Contest 2', '2024-01-28', 120),
(3, 'Monthly Challenge', '2024-02-01', 180);

-- Contest Participation
INSERT INTO ContestParticipation (student_id, contest_id, score, rank) VALUES
(1, 1, 80, 2),
(2, 1, 60, 5),
(3, 1, 70, 3),
(11, 1, 90, 1),
(12, 1, 50, 7),
(1, 2, 85, 1),
(11, 2, 75, 3),
(3, 2, 80, 2);

-- Clubs
INSERT INTO Club (id, name, description, center_id) VALUES
(1, 'Coding Club', 'Competitive programming and hackathons', 1),
(2, 'Robotics Club', 'Building robots and IoT projects', 1),
(3, 'Coding Club', 'Competitive programming and hackathons', 2),
(4, 'AI/ML Club', 'Artificial Intelligence research', 2);

-- Club Members
INSERT INTO ClubMember (student_id, club_id, role, joined_date) VALUES
(1, 1, 'president', '2024-01-20'),
(2, 1, 'member', '2024-01-22'),
(3, 1, 'member', '2024-01-22'),
(4, 2, 'president', '2024-01-25'),
(5, 2, 'member', '2024-01-25'),
(11, 3, 'president', '2024-02-05'),
(12, 3, 'member', '2024-02-05'),
(13, 3, 'member', '2024-02-05'),
(14, 4, 'president', '2024-02-10'),
(15, 4, 'member', '2024-02-10'),
(16, 4, 'member', '2024-02-10');

-- Placements
INSERT INTO Placement (student_id, company_name, role_title, package_lpa, placement_date, status) VALUES
(1, 'Google', 'Software Engineer', 25.0, '2024-06-01', 'accepted'),
(2, 'Microsoft', 'SDE-1', 18.0, '2024-06-05', 'accepted'),
(3, 'Amazon', 'SDE-1', 16.0, '2024-06-10', 'offered'),
(4, 'Infosys', 'Systems Engineer', 5.5, '2024-05-15', 'accepted'),
(5, 'TCS', 'Developer', 4.5, '2024-05-20', 'accepted'),
(11, 'Google', 'Software Engineer', 28.0, '2024-06-01', 'accepted'),
(12, 'Flipkart', 'SDE-1', 14.0, '2024-06-08', 'accepted'),
(13, 'Wipro', 'Developer', 5.0, '2024-05-25', 'rejected'),
(14, 'Adobe', 'MTS', 20.0, '2024-06-12', 'offered');

-- Projects
INSERT INTO Project (student_id, title, description, tech_stack, submitted_date, score) VALUES
(1, 'Chat Application', 'Real-time messaging app', 'React, Node.js, Socket.io', '2024-03-15', 92.0),
(2, 'E-commerce Platform', 'Online shopping portal', 'Django, PostgreSQL, React', '2024-03-15', 85.0),
(3, 'Weather App', 'Weather forecasting tool', 'Flutter, OpenWeather API', '2024-03-15', 78.0),
(11, 'ML Pipeline', 'Automated ML training pipeline', 'Python, TensorFlow, Docker', '2024-03-20', 95.0),
(12, 'Portfolio Website', 'Personal portfolio', 'HTML, CSS, JavaScript', '2024-03-20', 70.0);

-- Certifications
INSERT INTO Certification (student_id, name, issuing_org, issue_date, expiry_date) VALUES
(1, 'AWS Cloud Practitioner', 'Amazon Web Services', '2024-02-01', '2027-02-01'),
(1, 'Google Data Analytics', 'Google', '2024-03-01', NULL),
(2, 'Azure Fundamentals', 'Microsoft', '2024-02-15', '2027-02-15'),
(11, 'TensorFlow Developer', 'Google', '2024-01-15', NULL),
(11, 'AWS Solutions Architect', 'Amazon Web Services', '2024-03-01', '2027-03-01'),
(14, 'Oracle Java SE', 'Oracle', '2024-02-20', '2027-02-20');
