import streamlit as st
import time
import pandas as pd
from backend import (
    init_db, seed_data,
    register_student, login_student, get_student,
    get_all_exams, get_exam, delete_exam, save_exam, update_exam,
    save_result, get_student_results, get_exam_results, get_all_results,
    has_attempted, student_analytics, topic_scores,
    leaderboard_report, student_history_report,
    get_all_students, MCQQuestion, ShortAnswerQuestion
)

st.set_page_config(
    page_title="ExamPro",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stApp"] {
    background: #0f1117;
    font-family: 'Inter', sans-serif;
    color: #e8eaf0;
}
[data-testid="stSidebar"] { background: #1a1d27 !important; }
[data-testid="stMetricValue"] { color: #6c63ff !important; font-weight: 700; }

.stButton > button {
    background: #6c63ff !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stTextInput input, .stTextArea textarea {
    background: #1e2130 !important;
    color: #e8eaf0 !important;
    border: 1px solid #2e3250 !important;
    border-radius: 8px !important;
}
.stRadio label, .stSelectbox label { color: #e8eaf0 !important; }
.stTabs [data-baseweb="tab"] { color: #8b92a9 !important; }
.stTabs [aria-selected="true"] { color: #6c63ff !important; }

.card {
    background: #1e2130;
    border: 1px solid #2e3250;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}
.card-blue  { border-left: 4px solid #6c63ff; }
.card-green { border-left: 4px solid #00d4aa; }
.card-red   { border-left: 4px solid #ff4f6e; }
.card-yellow{ border-left: 4px solid #ffb347; }

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-blue   { background: rgba(108,99,255,0.2); color: #6c63ff; }
.badge-green  { background: rgba(0,212,170,0.2);  color: #00d4aa; }
.badge-red    { background: rgba(255,79,110,0.2); color: #ff4f6e; }
.badge-yellow { background: rgba(255,179,71,0.2); color: #ffb347; }

.hint-box {
    background: #1a2340;
    border: 1px solid #2e3250;
    border-left: 4px solid #6c63ff;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-top: 1rem;
    font-size: 0.82rem;
    color: #8b92a9;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def startup():
    init_db()
    seed_data()

startup()

# Session state defaults
for k, v in {"logged_in": False, "student_id": None, "student_name": "",
              "is_admin": False, "page": "home", "active_exam": None,
              "exam_start": None, "exam_answers": {}, "exam_done": False,
              "last_card": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

STUDENT_KEYWORD = "student" 
TEACHER_KEYWORD = "teacher"  

with st.sidebar:
    st.markdown("## 🎓 ExamPro")
    st.markdown("---")

    if st.session_state.logged_in:
        role = "Teacher" if st.session_state.is_admin else "🎓 Student"
        st.markdown(f"**{st.session_state.student_name}**  \n{role}")
        st.markdown("---")

        nav_items = [("Dashboard", "home"), ("Exams", "exams"),
                     ("My Results", "results"), ("Analytics", "analytics")]
        if st.session_state.is_admin:
            nav_items.append(("Teacher Panel", "admin"))

        for label, key in nav_items:
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state.page = key
                st.rerun()

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for k in ["logged_in","student_id","student_name","is_admin","active_exam",
                      "exam_start","exam_answers","exam_done","last_card"]:
                st.session_state[k] = False if k=="logged_in" else None
            st.session_state.page = "home"
            st.rerun()
    else:
        if st.button("Home",     use_container_width=True): st.session_state.page = "home";  st.rerun()
        if st.button("Login",    use_container_width=True): st.session_state.page = "auth";  st.rerun()

    st.markdown("---")
    
def go(page):
    st.session_state.page = page
    st.rerun()

def grade_color(grade):
    return {"A+":"green","A":"green","B":"blue","C":"yellow","D":"yellow","F":"red"}.get(grade,"blue")


def page_home():
    if st.session_state.logged_in:
        sid = st.session_state.student_id
        st.markdown(f"## 👋 Welcome back, {st.session_state.student_name}!")

        if st.session_state.is_admin:
            st.info("You're logged in as a **Teacher**. Use the Teacher Panel to manage exams.")
            if st.button("Go to Teacher Panel"): go("admin")
            return

        analytics = student_analytics(sid)
        exams = get_all_exams()
        pending = sum(1 for e in exams if not has_attempted(sid, e["exam_id"]))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Exams Taken",   analytics["total"]   if analytics else 0)
        c2.metric("Average Score", f"{analytics['average']}%" if analytics else "—")
        c3.metric("Best Score",    f"{analytics['highest']}%" if analytics else "—")
        c4.metric("Pending Exams", pending)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Available Exams")
            for exam in exams:
                done = has_attempted(sid, exam["exam_id"])
                status = "Done" if done else "▶ Start"
                color  = "green"  if done else "blue"
                st.markdown(f"""
                <div class="card card-{'green' if done else 'blue'}">
                    <b>{exam['title']}</b><br>
                    <span style="color:#8b92a9; font-size:0.85rem;">
                        {exam['subject']} · ⏱ {exam['duration_minutes']} min · {exam['total_marks']} marks
                    </span>
                    <span class="badge badge-{color}" style="float:right;">{status}</span>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            st.markdown("#### Recent Results")
            results = get_student_results(sid)[:5]
            if not results:
                st.info("No results yet. Take an exam!")
            for r in results:
                exam = get_exam(r["exam_id"])
                gc = grade_color(r["grade"])
                st.markdown(f"""
                <div class="card card-{gc}">
                    <b>{exam['title'] if exam else r['exam_id']}</b>
                    <span class="badge badge-{gc}" style="float:right;">{r['grade']}</span><br>
                    <span style="color:#8b92a9; font-size:0.85rem;">
                        {r['total_score']}/{r['total_marks']} · {r['percentage']}% · {r['submitted_at']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        ## 🎓 ExamPro 
        #### Online Examination System
        Timed assessments · Auto-grading · Instant analytics
        """)
        c1, c2, c3 = st.columns(3)
        for col, icon, title, desc in [
            (c1, "⏱️", "Timed Exams",   "Countdown timer with auto-submit"),
            (c2, "🤖", "Auto Grading",  "MCQ + keyword-based short answer"),
            (c3, "📊", "Analytics",     "Topic breakdown & grade reports"),
        ]:
            with col:
                st.markdown(f"""
                <div class="card card-blue" style="text-align:center; padding:1.5rem;">
                    <div style="font-size:2rem;">{icon}</div>
                    <b>{title}</b><br>
                    <span style="color:#8b92a9; font-size:0.85rem;">{desc}</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col, _ = st.columns([1,2])
        with col:
            if st.button("Get Started", use_container_width=True): go("auth")

def page_auth():
    st.markdown("## Login")
    col, _ = st.columns([1.2, 1])
    with col:
        username = st.text_input("Username", placeholder="e.g. student_ali  or  teacher_sara")
        password = st.text_input("Password", type="password", placeholder="Any password you choose")

        if st.button("Login", use_container_width=True):
            if not username.strip() or not password.strip():
                st.error("Please enter both username and password.")
            else:
                u = username.strip().lower()
                has_student = STUDENT_KEYWORD in u
                has_teacher = TEACHER_KEYWORD in u

                if not has_student and not has_teacher:
                    st.error(
                        f"Your username must contain **'{STUDENT_KEYWORD}'** (for student access) "
                        f"or **'{TEACHER_KEYWORD}'** (for teacher access)."
                    )
                elif has_teacher:
                    display_name = username.strip()
                    st.session_state.logged_in    = True
                    st.session_state.student_id   = -1
                    st.session_state.student_name = display_name
                    st.session_state.is_admin     = True
                    go("admin")
                else:
                    display_name = username.strip()
                    fake_email = f"{username.strip().lower().replace(' ', '_')}@exampro.local"
                    from backend import register_student as _reg, login_student as _login, get_conn
                    with get_conn() as conn:
                        row = conn.execute(
                            "SELECT * FROM students WHERE email=?", (fake_email,)
                        ).fetchone()
                    if row:
                        student = dict(row)
                    else:
                        # Create new student record on first login
                        _reg(display_name, fake_email, password)
                        with get_conn() as conn:
                            row = conn.execute(
                                "SELECT * FROM students WHERE email=?", (fake_email,)
                            ).fetchone()
                        student = dict(row)

                    st.session_state.logged_in    = True
                    st.session_state.student_id   = student["student_id"]
                    st.session_state.student_name = student["name"]
                    st.session_state.is_admin     = False
                    go("home")

        # Hint card
        st.markdown(f"""
        <div class="hint-box">
            <b style="color:#6c63ff;">How to login:</b><br><br>
            <b>Student:</b> Your username must contain the word
            <code style="color:#00d4aa;">student</code>
            &nbsp;e.g. <code>student_ali</code>, <code>rameesha_student</code><br><br>
            <b>Teacher:</b> Your username must contain the word
            <code style="color:#00d4aa;">teacher</code>
            &nbsp;e.g. <code>teacher_sara</code>, <code>mr_teacher_ahmed</code><br><br>
        
            
        </div>
        """, unsafe_allow_html=True)
        
def page_exams():
    st.markdown("## Available Exams")
    sid   = st.session_state.student_id
    exams = get_all_exams()

    if not exams:
        st.info("No exams available yet. Ask your teacher to create one!")
        return

    for exam in exams:
        done = has_attempted(sid, exam["exam_id"])
        topics = list({q.topic for q in exam["questions"]})
        topic_badges = " ".join(f'<span class="badge badge-blue">{t}</span>' for t in topics)

        st.markdown(f"""
        <div class="card card-{'green' if done else 'blue'}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <b style="font-size:1.05rem;">{exam['title']}</b><br>
                    <span style="color:#8b92a9; font-size:0.85rem;">
                            {exam['subject']} &nbsp;|&nbsp;
                            {len(exam['questions'])} questions &nbsp;|&nbsp;
                            {exam['duration_minutes']} min &nbsp;|&nbsp;
                            {exam['total_marks']} marks
                    </span><br>
                    <div style="margin-top:0.4rem;">{topic_badges}</div>
                </div>
                <div>{'<span class="badge badge-green">Completed</span>' if done else ''}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, _ = st.columns([1, 1, 3])
        with col1:
            if not done:
                if st.button("▶ Start", key=f"start_{exam['exam_id']}", use_container_width=True):
                    st.session_state.active_exam   = exam["exam_id"]
                    st.session_state.exam_start    = time.time()
                    st.session_state.exam_answers  = {}
                    st.session_state.exam_done     = False
                    go("take_exam")
        with col2:
            if done:
                if st.button("Result", key=f"res_{exam['exam_id']}", use_container_width=True):
                    go("results")


def page_take_exam():
    exam_id = st.session_state.active_exam
    sid     = st.session_state.student_id

    if not exam_id:
        st.error("No exam selected."); go("exams"); return

    if has_attempted(sid, exam_id):
        st.warning("Already completed."); go("results"); return

    if st.session_state.exam_done and st.session_state.last_card:
        _show_result_card(st.session_state.last_card)
        return

    exam     = get_exam(exam_id)
    duration = exam["duration_minutes"] * 60
    elapsed  = time.time() - st.session_state.exam_start
    remaining = max(0, duration - elapsed)

    if remaining == 0:
        _submit(exam, sid)
        st.rerun()
        return

    mins = int(remaining // 60)
    secs = int(remaining % 60)
    timer_color = "#ff4f6e" if remaining < 120 else ("#ffb347" if remaining < 300 else "#00d4aa")

    st.markdown(f"""
    <div class="card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <div>
            <b style="font-size:1.1rem;">{exam['title']}</b><br>
            <span style="color:#8b92a9; font-size:0.85rem;">{exam['subject']} · {len(exam['questions'])} questions · {exam['total_marks']} marks</span>
        </div>
        <div style="text-align:center;">
            <div style="color:#8b92a9; font-size:0.75rem; letter-spacing:1px;">TIME LEFT</div>
            <div style="font-size:2rem; font-weight:700; color:{timer_color}; font-family:monospace;">{mins:02d}:{secs:02d}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(min(elapsed / duration, 1.0))

    answers = st.session_state.exam_answers
    st.markdown("---")

    for i, q in enumerate(exam["questions"]):
        qid = str(q.qid)
        type_color = "blue" if q.q_type == "MCQ" else "green"

        st.markdown(f"""
        <div class="card card-blue">
            <div style="display:flex; justify-content:space-between;">
                <b>Q{i+1}. {q.text}</b>
                <div>
                    <span class="badge badge-{type_color}">{q.q_type}</span>
                    <span class="badge badge-yellow" style="margin-left:4px;">{q.marks} marks</span>
                    <span class="badge badge-green" style="margin-left:4px;">{q.topic}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if q.q_type == "MCQ":
            opts = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(q.options)]
            cur  = answers.get(qid)
            idx  = ["A","B","C","D"].index(cur) if cur in ["A","B","C","D"] else None
            chosen = st.radio("", opts, index=idx, key=f"q_{qid}", label_visibility="collapsed")
            if chosen:
                answers[qid] = chosen[0]
        else:
            answers[qid] = st.text_area("Your answer:", value=answers.get(qid,""),
                                         key=f"q_{qid}", height=90, label_visibility="collapsed")
        st.markdown("")

    st.session_state.exam_answers = answers

    n_done = sum(1 for q in exam["questions"] if answers.get(str(q.qid),"").strip())
    st.caption(f"{n_done} of {len(exam['questions'])} answered")

    col, _ = st.columns([1, 2])
    with col:
        if st.button("Submit Exam", use_container_width=True, type="primary"):
            _submit(exam, sid)
            st.rerun()

    time.sleep(1)
    st.rerun()


def _submit(exam, sid):
    answers = st.session_state.exam_answers
    scores  = {}
    total   = 0
    for q in exam["questions"]:
        qid = str(q.qid)
        awarded = q.grade(answers.get(qid, ""))
        scores[qid] = awarded
        total += awarded

    time_taken = int(time.time() - st.session_state.exam_start)
    save_result(sid, exam["exam_id"], answers, scores, total, exam["total_marks"], time_taken)

    card = {"exam": exam, "answers": answers, "scores": scores,
            "total": total, "total_marks": exam["total_marks"],
            "time_taken": time_taken}
    st.session_state.last_card  = card
    st.session_state.exam_done  = True
    st.session_state.exam_start = None


def _show_result_card(card):
    pct   = round(card["total"] / card["total_marks"] * 100, 1) if card["total_marks"] else 0
    grade = ("A+" if pct>=90 else "A" if pct>=80 else "B" if pct>=70 else
             "C" if pct>=60 else "D" if pct>=50 else "F")
    passed = pct >= 50
    gc     = grade_color(grade)

    st.markdown(f"""
    <div style="text-align:center; padding:1.5rem 0;">
        <div style="font-size:3rem;">{"🎉" if passed else "📚"}</div>
        <h2 style="color:{'#00d4aa' if passed else '#ff4f6e'};">
            {"You Passed!" if passed else "Better luck next time!"}
        </h2>
        <p style="color:#8b92a9;">{card['exam']['title']}</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    m, s = divmod(card["time_taken"], 60)
    c1.metric("Score",      f"{card['total']}/{card['total_marks']}")
    c2.metric("Percentage", f"{pct}%")
    c3.metric("Grade",      grade)
    c4.metric("Time Taken", f"{m}m {s}s")

    st.markdown("### Question Breakdown")
    for q in card["exam"]["questions"]:
        qid     = str(q.qid)
        awarded = card["scores"].get(qid, 0)
        correct = awarded == q.marks
        icon    = "✅" if correct else ("🟡" if awarded > 0 else "❌")
        answer  = card["answers"].get(qid, "") or "(no answer)"

        with st.expander(f"{icon} Q{q.qid}: {q.text[:70]}... — {awarded}/{q.marks} marks"):
            st.markdown(f"**Your answer:** {answer}")
            if q.q_type == "MCQ":
                st.markdown(f"**Correct answer:** {q.options[q.correct_index]}")
            else:
                st.markdown(f"**Sample answer:** {q.sample_answer}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Take Another Exam", use_container_width=True):
            st.session_state.exam_done = False
            go("exams")
    with col2:
        if st.button("View All Results", use_container_width=True):
            st.session_state.exam_done = False
            go("results")

def page_results():
    st.markdown("## My Results")
    sid     = st.session_state.student_id
    results = get_student_results(sid)

    if not results:
        st.info("No results yet. Take an exam!")
        if st.button("Browse Exams"): go("exams")
        return

    avg = round(sum(r["percentage"] for r in results) / len(results), 1)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Exams",  len(results))
    c2.metric("Average Score", f"{avg}%")
    c3.metric("Passed",  sum(1 for r in results if r["passed"]))
    c4.metric("Best",    f"{max(r['percentage'] for r in results)}%")

    st.markdown("---")
    for r in results:
        exam = get_exam(r["exam_id"])
        gc   = grade_color(r["grade"])
        icon = "✅" if r["passed"] else "❌"
        m, s = divmod(r["time_taken_seconds"], 60)

        with st.expander(f"{icon} {exam['title'] if exam else r['exam_id']}  |  {r['percentage']}%  |  Grade: {r['grade']}  |  {r['submitted_at']}"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Score",  f"{r['total_score']}/{r['total_marks']}")
            c2.metric("%",       f"{r['percentage']}%")
            c3.metric("Grade",   r["grade"])
            c4.metric("Time",    f"{m}m {s}s")

            if exam:
                st.markdown("**Per-question breakdown:**")
                for q in exam["questions"]:
                    qid     = str(q.qid)
                    awarded = r["scores"].get(qid, 0)
                    correct = awarded == q.marks
                    color   = "#00d4aa" if correct else ("#ffb347" if awarded > 0 else "#ff4f6e")
                    icon2   = "✅" if correct else ("🟡" if awarded > 0 else "❌")
                    answer  = r["answers"].get(qid, "") or "(blank)"
                    st.markdown(f"""
                    <div class="card card-{'green' if correct else 'red'}" style="padding:0.6rem 1rem; margin-bottom:0.4rem;">
                        <b>{icon2} Q{q.qid}</b>
                        <span class="badge badge-blue" style="margin-left:6px;">{q.topic}</span>
                        <span style="float:right; color:{color}; font-weight:700;">{awarded}/{q.marks}</span><br>
                        <span style="color:#8b92a9; font-size:0.82rem;">Answer: {str(answer)[:120]}</span>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📄 Download Text Report"):
        report = student_history_report(sid)
        st.code(report, language="text")

def page_analytics():
    st.markdown("## My Analytics")
    sid      = st.session_state.student_id
    analytics = student_analytics(sid)

    if not analytics:
        st.info("Complete at least one exam to see analytics.")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Exams Taken",  analytics["total"])
    c2.metric("Average",      f"{analytics['average']}%")
    c3.metric("Best",         f"{analytics['highest']}%")
    c4.metric("Lowest",       f"{analytics['lowest']}%")
    c5.metric("Passed",       analytics["passed"])

    st.markdown("---")
    results = get_student_results(sid)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Score History")
        chart_rows = []
        for r in reversed(results):
            exam = get_exam(r["exam_id"])
            chart_rows.append({
                "Exam": exam["title"][:20] if exam else str(r["exam_id"]),
                "Score (%)": r["percentage"],
                "Pass Line": 50
            })
        df = pd.DataFrame(chart_rows)
        st.line_chart(df.set_index("Exam"))

    with col2:
        st.markdown("#### Topic Performance")
        topics = topic_scores(sid)
        if topics:
            df_t = pd.DataFrame({"Topic": list(topics.keys()), "Avg %": list(topics.values())})
            st.bar_chart(df_t.set_index("Topic"))

    st.markdown("---")
    st.markdown("#### All Results Table")
    rows = []
    for r in results:
        exam = get_exam(r["exam_id"])
        m, s = divmod(r["time_taken_seconds"], 60)
        rows.append({
            "Exam":    exam["title"] if exam else "—",
            "Score":   f"{r['total_score']}/{r['total_marks']}",
            "%":       f"{r['percentage']}%",
            "Grade":   r["grade"],
            "Status":  "Pass ✅" if r["passed"] else "Fail ❌",
            "Time":    f"{m}m {s}s",
            "Date":    r["submitted_at"]
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    weak = {t: v for t, v in topics.items() if v < 60}
    if weak:
        st.markdown("#### Topics Needing Improvement")
        for topic, avg in sorted(weak.items(), key=lambda x: x[1]):
            st.markdown(f"""
            <div class="card card-red">
                <div style="display:flex; justify-content:space-between;">
                    <b>{topic}</b> <span style="color:#ff4f6e;">{avg}% avg</span>
                </div>
                <div style="background:#2e3250; border-radius:6px; height:8px; margin-top:0.5rem;">
                    <div style="background:#ff4f6e; width:{avg}%; height:100%; border-radius:6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def page_admin():
    st.markdown("## Teacher Panel")
    tab1, tab2, tab3 = st.tabs(["Overview", "Create Exam", "Manage & Edit Exams"])

    with tab1:
        exams    = get_all_exams()
        students = get_all_students()
        results  = get_all_results()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Exams",    len(exams))
        c2.metric("Students", len(students))
        c3.metric("Attempts", len(results))
        avg = round(sum(r["percentage"] for r in results)/len(results),1) if results else 0
        c4.metric("Avg Score", f"{avg}%")

        if results:
            st.markdown("---\n**All Submissions**")
            rows = []
            for r in results:
                exam    = get_exam(r["exam_id"])
                student = get_student(r["student_id"])
                m, s    = divmod(r["time_taken_seconds"], 60)
                rows.append({
                    "Student": student["name"] if student else "?",
                    "Exam":    exam["title"] if exam else "?",
                    "Score":   f"{r['total_score']}/{r['total_marks']}",
                    "%":       f"{r['percentage']}%",
                    "Grade":   r["grade"],
                    "Status":  "Pass" if r["passed"] else "Fail",
                    "Date":    r["submitted_at"]
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("---\n**Exam Leaderboards**")
        for exam in exams:
            with st.expander(f"🏆 {exam['title']}"):
                st.code(leaderboard_report(exam["exam_id"]), language="text")

    with tab2:
        st.markdown("#### Create a New Exam")
        title    = st.text_input("Exam Title",   placeholder="e.g. Python Quiz")
        subject  = st.text_input("Subject",      placeholder="e.g. Computer Science")
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=180, value=20)

        st.markdown("---")
        n_mcq = st.number_input("Number of MCQ Questions",          min_value=0, max_value=20, value=3)
        n_sa  = st.number_input("Number of Short Answer Questions",  min_value=0, max_value=15, value=1)

        questions = []
        qid = 1

        if n_mcq > 0:
            st.markdown("**MCQ Questions**")
        for i in range(int(n_mcq)):
            with st.expander(f"MCQ {i+1}", expanded=(i==0)):
                qt    = st.text_input("Question",   key=f"mt_{i}")
                topic = st.text_input("Topic",      key=f"mto_{i}", placeholder="e.g. OOP")
                marks = st.number_input("Marks",    key=f"mm_{i}", min_value=1, max_value=10, value=2)
                opts  = [st.text_input(f"Option {chr(65+j)}", key=f"mo_{i}_{j}") for j in range(4)]
                correct = st.selectbox("Correct Answer", ["A","B","C","D"], key=f"mc_{i}")
                questions.append(("MCQ", qid, qt, topic, marks, opts, ["A","B","C","D"].index(correct)))
                qid += 1

        if n_sa > 0:
            st.markdown("**Short Answer Questions**")
        for i in range(int(n_sa)):
            with st.expander(f"Short Answer {i+1}", expanded=(i==0)):
                qt    = st.text_input("Question",         key=f"st_{i}")
                topic = st.text_input("Topic",            key=f"sto_{i}", placeholder="e.g. Algorithms")
                marks = st.number_input("Marks",          key=f"sm_{i}", min_value=1, max_value=20, value=5)
                kws   = st.text_input("Keywords (comma-separated)", key=f"sk_{i}", placeholder="loop, iterate, repeat")
                sample = st.text_area("Sample Answer",   key=f"ss_{i}", height=70)
                questions.append(("SA", qid, qt, topic, marks, kws, sample))
                qid += 1

        if st.button("Save Exam", type="primary", key="create_save"):
            if not title or not subject or not questions:
                st.error("Title, subject and at least one question are required.")
            else:
                q_objects = []
                for q in questions:
                    if q[0] == "MCQ":
                        _, qid2, qt2, topic2, marks2, opts2, cidx = q
                        q_objects.append(MCQQuestion(qid2, qt2, marks2, topic2, opts2, cidx))
                    else:
                        _, qid2, qt2, topic2, marks2, kws2, sample2 = q
                        kw_list = [k.strip() for k in kws2.split(",") if k.strip()]
                        q_objects.append(ShortAnswerQuestion(qid2, qt2, marks2, topic2, kw_list, sample2))
                save_exam(title, subject, duration, q_objects)
                st.success(f"Exam '{title}' created!")
                st.rerun()

    with tab3:
        exams = get_all_exams()
        for exam in exams:
            exam_results = get_exam_results(exam["exam_id"])
            avg_e = round(sum(r["percentage"] for r in exam_results)/len(exam_results),1) if exam_results else 0

            with st.expander(f"{exam['title']}  |  {exam['subject']}  |  {len(exam_results)} attempts"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Questions",   len(exam["questions"]))
                c2.metric("Total Marks", exam["total_marks"])
                c3.metric("Duration",    f"{exam['duration_minutes']} min")
                c4.metric("Avg Score",   f"{avg_e}%" if exam_results else "—")

                st.markdown("---")
                st.markdown("#### Edit Exam Settings")

                eid = exam["exam_id"]

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    new_title = st.text_input("Exam Title", value=exam["title"],
                                               key=f"edit_title_{eid}")
                with col_b:
                    new_subject = st.text_input("Subject", value=exam["subject"],
                                                 key=f"edit_subj_{eid}")
                with col_c:
                    new_duration = st.number_input(
                        "⏱️ Time Limit (minutes)",
                        min_value=1, max_value=300,
                        value=exam["duration_minutes"],
                        key=f"edit_dur_{eid}"
                    )

                st.markdown("**Edit Questions** (change marks, topic, or question text)")
                new_questions = []
                q_valid = True
                for i, q in enumerate(exam["questions"]):
                    with st.expander(f"Q{i+1}: {q.text[:60]}...", expanded=False):
                        new_qtext = st.text_input("Question Text", value=q.text,
                                                   key=f"edit_qt_{eid}_{i}")
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            new_topic = st.text_input("Topic", value=q.topic,
                                                       key=f"edit_topic_{eid}_{i}")
                        with ec2:
                            new_marks = st.number_input("Marks", min_value=1, max_value=20,
                                                         value=q.marks,
                                                         key=f"edit_marks_{eid}_{i}")
                        if q.q_type == "MCQ":
                            new_opts = []
                            for j, opt in enumerate(q.options):
                                new_opts.append(st.text_input(
                                    f"Option {chr(65+j)}", value=opt,
                                    key=f"edit_opt_{eid}_{i}_{j}"
                                ))
                            new_correct = st.selectbox(
                                "Correct Answer",
                                ["A","B","C","D"],
                                index=q.correct_index,
                                key=f"edit_correct_{eid}_{i}"
                            )
                            new_questions.append(MCQQuestion(
                                q.qid, new_qtext, new_marks, new_topic,
                                new_opts, ["A","B","C","D"].index(new_correct)
                            ))
                        else:
                            kw_str = ", ".join(q.keywords)
                            new_kws = st.text_input("Keywords (comma-separated)", value=kw_str,
                                                     key=f"edit_kw_{eid}_{i}")
                            new_sample = st.text_area("Sample Answer", value=q.sample_answer,
                                                       key=f"edit_sa_{eid}_{i}", height=70)
                            kw_list = [k.strip() for k in new_kws.split(",") if k.strip()]
                            new_questions.append(ShortAnswerQuestion(
                                q.qid, new_qtext, new_marks, new_topic, kw_list, new_sample
                            ))

                col_save, col_del = st.columns(2)
                with col_save:
                    if st.button("💾 Save Changes", key=f"save_edit_{eid}", use_container_width=True):
                        if not new_title.strip() or not new_subject.strip():
                            st.error("Title and subject cannot be empty.")
                        else:
                            update_exam(eid, new_title, new_subject, new_duration, new_questions)
                            st.success("Exam updated successfully!")
                            st.rerun()

                with col_del:
                    if st.button("🗑️ Delete Exam", key=f"del_{eid}", use_container_width=True):
                        delete_exam(eid)
                        st.success("Deleted.")
                        st.rerun()


page = st.session_state.page

if page == "home":
    page_home()
elif page == "auth":
    page_auth()
elif page == "exams":
    if not st.session_state.logged_in: st.warning("Please login first."); page_auth()
    else: page_exams()
elif page == "take_exam":
    if not st.session_state.logged_in: st.warning("Please login first.")
    else: page_take_exam()
elif page == "results":
    if not st.session_state.logged_in: st.warning("Please login first.")
    else: page_results()
elif page == "analytics":
    if not st.session_state.logged_in: st.warning("Please login first.")
    else: page_analytics()
elif page == "admin":
    if not st.session_state.is_admin: st.error("Access denied.")
    else: page_admin()
