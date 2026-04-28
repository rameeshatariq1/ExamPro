# Online Examination & Result System

A web-based exam platform built with Python and Streamlit. Students can take timed MCQ and short-answer exams, and teachers can create, edit, and monitor them, all through a browser interface with no separate server setup required.

---

## Features

**For Students**
- Login with any username (must contain the word `student`) and any password
- Take timed exams with an auto-submit countdown
- View scores, grades, and per-question breakdown immediately after submission
- Track performance over time through an analytics dashboard

**For Teachers**
- Login with any username containing the word `teacher`
- Create exams with MCQ and short-answer questions
- Set time limits, marks per question, and topics
- Edit any exam after creation - title, subject, duration, questions, options, correct answers
- View all student submissions and per-exam leaderboards

---

## Project Structure

```
exam_system/
├── app.py            # Frontend all Streamlit pages and UI
├── backend.py        # Backend database, OOP classes, grading logic
├── requirements.txt  # Python dependencies
└── README.md
```

The database (`exam_system.db`) and log file (`exam_system.log`) are created automatically on first run.

---

## OOP Concepts Used

This project was built as a demonstration of core Object-Oriented Programming concepts.

| Concept | Where Used |
|---|---|
| Abstract Class | `Question` base class with abstract `grade()` method |
| Inheritance | `MCQQuestion` and `ShortAnswerQuestion` both extend `Question` |
| Singleton Pattern | `ExamLogger` only one logger instance exists throughout runtime |
| Encapsulation | All DB logic is encapsulated inside backend functions |
| Polymorphism | `grade()` behaves differently for MCQ vs short-answer questions |

---
## Setup & Installation

**Requirements:** Python 3.9 or higher

**Step 1 Clone or download the project**
```
exam_system/
├── app.py
├── backend.py
└── requirements.txt
```

**Step 2 Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 3 Run the app**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---
## Live Demo

Deployed on Streamlit Community Cloud: [Examprooo](https://examprooo.streamlit.app/)

---
## Dependencies

| Package | Version | Purpose |
|---|---|---|
| streamlit | >=1.32.0 | Web UI framework |
| pandas | >=2.0.0 | Data tables and charts |
| tabulate | >=0.9.0 | Text-based leaderboard reports |

SQLite is used for the database it is part of Python's standard library and requires no separate installation.

---

## Database Schema

Three tables are created automatically:

**students**
- `student_id`, `name`, `email`, `password_hash`, `created_at`

**exams**
- `exam_id`, `title`, `subject`, `duration_minutes`, `questions_json`, `created_at`

**results**
- `result_id`, `student_id`, `exam_id`, `answers_json`, `scores_json`, `total_score`, `total_marks`, `time_taken_seconds`, `submitted_at`

Questions are stored as JSON inside the `exams` table. Each result stores the student's answers and per-question scores as JSON as well.

---

## Grading Logic

**MCQ:** Full marks if the selected option matches the correct answer. Zero otherwise.

**Short Answer:** The student's response is checked for the presence of keywords defined by the teacher. Marks are awarded proportionally based on how many keywords appear in the answer.

Grade boundaries:

| Grade | Percentage |
|---|---|
| A+ | 90% and above |
| A  | 80 – 89% |
| B  | 70 – 79% |
| C  | 60 – 69% |
| D  | 50 – 59% |
| F  | Below 50% |

---

