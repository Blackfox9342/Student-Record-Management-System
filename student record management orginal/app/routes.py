import io
from datetime import datetime

from flask import Blueprint, abort, redirect, render_template, send_file, url_for
from flask_login import current_user, login_required
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models import verify_academic_ledger

main_bp = Blueprint("main", __name__)


STUDENT_MARKS = [
    {"subject": "Database Systems", "cat1": 18, "cat2": 19, "assignment": 9, "total": 46, "grade": "A"},
    {"subject": "Web Development", "cat1": 17, "cat2": 20, "assignment": 10, "total": 47, "grade": "A"},
    {"subject": "Software Engineering", "cat1": 16, "cat2": 18, "assignment": 9, "total": 43, "grade": "B+"},
    {"subject": "Computer Networks", "cat1": 15, "cat2": 17, "assignment": 8, "total": 40, "grade": "B+"},
]

STUDENT_ATTENDANCE = [
    ("Database Systems", "Present", "100%"),
    ("Web Development", "Present", "98%"),
    ("Software Engineering", "Present", "96%"),
    ("Computer Networks", "Absent", "92%"),
]

FACULTY_CLASSES = [
    ("09:00", "Web Development", "III CSE A", "48 students"),
    ("11:00", "Database Systems", "III CSE B", "46 students"),
    ("02:00", "Project Lab", "IV CSE A", "24 students"),
]

MODULE_BOOKS = {
    1: {
        "title": "Module 1 - Fundamentals of Database Systems",
        "topics": [
            "Database concepts and data models",
            "ER modeling and normalization basics",
            "Relational schema design",
            "SQL fundamentals",
        ],
        "references": [
            "Korth, Database System Concepts",
            "Elmasri and Navathe, Fundamentals of Database Systems",
        ],
    },
    2: {
        "title": "Module 2 - Advanced SQL and Constraints",
        "topics": [
            "Joins and subqueries",
            "Views, indexes, and stored procedures",
            "Transactions and ACID properties",
            "Integrity constraints",
        ],
        "references": [
            "Ramakrishnan, Database Management Systems",
            "Silberschatz, Database System Concepts",
        ],
    },
    3: {
        "title": "Module 3 - Web Development Core",
        "topics": [
            "HTML5 semantic structure",
            "CSS3 layout and responsive design",
            "JavaScript fundamentals",
            "Client-server flow",
        ],
        "references": [
            "MDN Web Docs",
            "Eloquent JavaScript by Marijn Haverbeke",
        ],
    },
    4: {
        "title": "Module 4 - Backend with Flask",
        "topics": [
            "Flask app structure",
            "Routing and templates",
            "Authentication with Flask-Login",
            "Form handling and validation",
        ],
        "references": [
            "Flask Official Documentation",
            "Miguel Grinberg, Flask Web Development",
        ],
    },
    5: {
        "title": "Module 5 - Academic Analytics",
        "topics": [
            "Attendance percentage calculations",
            "Internal marks processing",
            "GPA and CGPA computation",
            "Defaulter and topper analytics",
        ],
        "references": [
            "Institution Academic Handbook",
            "Chart.js Documentation",
        ],
    },
    6: {
        "title": "Module 6 - Reporting and Exports",
        "topics": [
            "PDF report generation with ReportLab",
            "Excel export with OpenPyXL",
            "Transcript formatting",
            "Bulk report workflows",
        ],
        "references": [
            "ReportLab User Guide",
            "OpenPyXL Documentation",
        ],
    },
    7: {
        "title": "Module 7 - Security and Audit",
        "topics": [
            "Role-based access control",
            "Password hashing",
            "Audit log structure",
            "Operational best practices",
        ],
        "references": [
            "OWASP Top 10",
            "Flask Security Patterns",
        ],
    },
}

STUDENT_MODULE_TITLES = [
    "Profile",
    "My Curriculum",
    "Course Registration",
    "Attendance Record",
    "Daily Attendance",
    "CAT 1 Marks",
    "CAT 2 Marks",
    "Assignment Marks",
    "Quiz Marks",
    "Lab Marks",
    "Practical Marks",
    "End Semester Marks",
    "Semester GPA",
    "Overall CGPA",
    "Rank Position",
    "Backlog Status",
    "Fee Summary",
    "Scholarship Details",
    "Notifications",
    "Time Table",
    "Exam Schedule",
    "Hall Ticket",
    "Transcript",
    "Marksheet Download",
    "Academic History",
    "Mentor Messages",
]

FACULTY_MODULE_TITLES = [
    "Faculty Profile",
    "Subject Allocation",
    "Attendance Entry",
    "Attendance Correction",
    "CAT 1 Entry",
    "CAT 2 Entry",
    "Assignment Entry",
    "Quiz Entry",
    "Lab Entry",
    "Practical Entry",
    "End Semester Entry",
    "Grade Finalization",
    "Defaulter List",
    "Class Advisor",
    "Proctor Notes",
    "Student Performance",
    "Department Reports",
    "Time Table",
    "Invigilation Duty",
    "Question Bank",
    "Course Plan",
    "CO Attainment",
    "Faculty Notifications",
    "Leave Request",
    "Faculty Workload",
    "Class Summary Download",
]

ADMIN_MODULE_TITLES = [
    "Admin Profile",
    "Student Master",
    "Faculty Master",
    "Department Master",
    "Program Master",
    "Semester Master",
    "Subject Master",
    "Enrollment Control",
    "Attendance Audit",
    "Marks Audit",
    "GPA Audit",
    "CGPA Audit",
    "Rank List",
    "Promotion Rules",
    "Transcript Control",
    "Report Center",
    "User Accounts",
    "Role Permissions",
    "Notification Center",
    "Fee Dashboard",
    "Scholarship Dashboard",
    "Placement Summary",
    "Event Management",
    "System Settings",
    "Audit Logs",
    "Backup and Restore",
]


def _slugify(text):
    return text.lower().replace(" ", "-")


def _student_assessment_rows(kind):
    key_map = {
        "cat1": "cat1",
        "cat2": "cat2",
        "assignment": "assignment",
        "quiz": "assignment",
        "lab": "assignment",
        "practical": "assignment",
        "endsem": "total",
    }
    key = key_map[kind]
    rows = []
    for item in STUDENT_MARKS:
        value = item[key]
        if kind == "quiz":
            value = min(10, max(6, value))
        if kind == "lab":
            value = min(20, value + 9)
        if kind == "practical":
            value = min(25, value + 11)
        if kind == "endsem":
            value = min(100, item["total"] + 44)
        rows.append([item["subject"], value, item["grade"], "Recorded"])
    return rows


def _module_content_for(role, slug, title, now):
    default = {
        "description": f"Detailed operational view for {title.lower()} in the {role.title()} portal.",
        "highlights": [
            f"Workflow checks enabled for {title}.",
            "Last sync completed without errors.",
            "Records validated against university policy.",
            "Export options are available for this module.",
        ],
        "columns": ["Item", "Value", "Status", "Remarks"],
        "rows": [
            ["Module", title, "Active", "Mapped to role workflow"],
            ["Last review", now, "OK", "Reviewed by operations"],
            ["Approval flow", "2-level", "Active", "HOD and Controller"],
            ["Data source", "Prakash ERP Core", "Connected", "Live sample records"],
            ["Export", "PDF / Excel", "Ready", "Single-click download"],
        ],
    }

    if role == "student":
        if slug == "profile":
            return {
                "description": "Personal profile, academic identity, and guardian details.",
                "columns": ["Field", "Value", "Status", "Remark"],
                "rows": [
                    ["Student Name", "Prakash", "Verified", "Profile complete"],
                    ["Register Number", "PU23CSE1842", "Verified", "Generated by registrar"],
                    ["Department", "Computer Science and Engineering", "Verified", "Current program"],
                    ["Program", "B.Tech CSE", "Verified", "2023-2027 batch"],
                    ["Mentor", "Dr. Priya Nair", "Assigned", "Mentor meetings monthly"],
                    ["Guardian", "Mr. Rajesh", "Verified", "Contact on file"],
                ],
                "highlights": [
                    "Profile data is synced with admission records.",
                    "Identity and contact details are verified.",
                    "Mentor mapping is currently active.",
                    "Update request workflow available via student section.",
                ],
            }
        if slug == "my-curriculum":
            return {
                "description": "Semester-wise curriculum and credits for your program.",
                "columns": ["Semester", "Core Subjects", "Electives", "Credits"],
                "rows": [["Sem 3", "5", "1", "21"], ["Sem 4", "4", "2", "22"], ["Sem 5", "5", "2", "24"]],
            }
        if slug == "course-registration":
            return {
                "description": "Current semester course registration status.",
                "columns": ["Subject", "Faculty", "Type", "Status"],
                "rows": [["Database Systems", "Dr. Priya Nair", "Core", "Registered"], ["Web Development", "Prof. A. Kumar", "Core", "Registered"], ["Cloud Basics", "Prof. R. Menon", "Elective", "Waitlisted"]],
            }
        if slug in {"attendance-record", "daily-attendance"}:
            return {
                "description": "Subject-wise attendance register with percentage and status.",
                "columns": ["Subject", "Status", "Attendance", "Remark"],
                "rows": [[subject, status, percent, "Safe" if percent != "92%" else "Watch"] for subject, status, percent in STUDENT_ATTENDANCE],
            }
        if slug == "cat-1-marks":
            return {"description": "CAT 1 marks with subject-wise grading.", "columns": ["Subject", "CAT 1", "Grade", "Status"], "rows": _student_assessment_rows("cat1")}
        if slug == "cat-2-marks":
            return {"description": "CAT 2 marks with subject-wise grading.", "columns": ["Subject", "CAT 2", "Grade", "Status"], "rows": _student_assessment_rows("cat2")}
        if slug == "assignment-marks":
            return {"description": "Assignment score details for all registered subjects.", "columns": ["Subject", "Assignment", "Grade", "Status"], "rows": _student_assessment_rows("assignment")}
        if slug == "quiz-marks":
            return {"description": "Quiz score details and recorded status.", "columns": ["Subject", "Quiz", "Grade", "Status"], "rows": _student_assessment_rows("quiz")}
        if slug == "lab-marks":
            return {"description": "Lab performance marks and grading.", "columns": ["Subject", "Lab", "Grade", "Status"], "rows": _student_assessment_rows("lab")}
        if slug == "practical-marks":
            return {"description": "Practical marks and consolidated grading.", "columns": ["Subject", "Practical", "Grade", "Status"], "rows": _student_assessment_rows("practical")}
        if slug == "end-semester-marks":
            return {"description": "End semester marks with current grade mapping.", "columns": ["Subject", "End Sem", "Grade", "Status"], "rows": _student_assessment_rows("endsem")}
        if slug == "semester-gpa":
            return {"description": "Current semester GPA calculation details.", "columns": ["Semester", "Credits", "Grade Points", "GPA"], "rows": [["Sem 3", "21", "183", "8.71"], ["Sem 4", "22", "192", "8.72"]]}
        if slug == "overall-cgpa":
            return {"description": "Overall CGPA summary up to current semester.", "columns": ["Semesters Counted", "Total Credits", "Total Points", "CGPA"], "rows": [["4", "84", "731", "8.70"]]}
        if slug == "rank-position":
            return {"description": "Department rank and cohort standing.", "columns": ["Department", "Batch Strength", "Your Rank", "Percentile"], "rows": [["CSE", "240", "12", "95.0"]]}
        if slug == "backlog-status":
            return {"description": "Backlog and arrear status for completed semesters.", "columns": ["Semester", "Subjects", "Backlogs", "Status"], "rows": [["Sem 1", "8", "0", "Clear"], ["Sem 2", "8", "0", "Clear"], ["Sem 3", "7", "0", "Clear"]]}
        if slug == "fee-summary":
            return {"description": "Tuition and fee payment status.", "columns": ["Term", "Amount", "Paid", "Status"], "rows": [["2026 Odd", "85000", "85000", "Paid"], ["Hostel", "42000", "42000", "Paid"], ["Exam Fee", "3500", "3500", "Paid"]]}
        if slug == "scholarship-details":
            return {"description": "Scholarship category, amount, and validity period.", "columns": ["Scheme", "Amount", "Duration", "Status"], "rows": [["Merit Scholarship", "25000", "2026-27", "Approved"]]}
        if slug == "notifications":
            return {"description": "Academic and exam related notices for student portal.", "columns": ["Date", "Category", "Message", "Status"], "rows": [["26 Jul", "Exam", "CAT 2 schedule published", "Unread"], ["25 Jul", "Academics", "Course registration open", "Read"], ["24 Jul", "Finance", "Fee receipt generated", "Read"]]}
        if slug == "time-table":
            return {"description": "Weekly class schedule.", "columns": ["Day", "09:00", "11:00", "14:00"], "rows": [["Mon", "Web Development", "Database Systems", "Project Lab"], ["Tue", "Software Engineering", "Networks", "Mentor Hour"], ["Wed", "Database Systems", "Web Development", "Library"]]}
        if slug == "exam-schedule":
            return {"description": "Upcoming internal and end semester exam schedule.", "columns": ["Date", "Exam", "Subject", "Session"], "rows": [["04 Aug", "CAT 2", "Database Systems", "FN"], ["06 Aug", "CAT 2", "Web Development", "AN"], ["11 Nov", "End Sem", "Software Engineering", "FN"]]}
        if slug == "hall-ticket":
            return {"description": "Hall ticket issue status and verification details.", "columns": ["Exam", "Ticket No", "Issued On", "Status"], "rows": [["CAT 2", "PUCAT22026CSE1842", "28 Jul", "Issued"], ["End Semester", "PUES2026CSE1842", "05 Nov", "Pending"]]}
        if slug == "transcript":
            return {"description": "Transcript summary with semester-grade trail.", "columns": ["Semester", "Credits", "GPA", "Result"], "rows": [["Sem 1", "20", "8.51", "Pass"], ["Sem 2", "21", "8.64", "Pass"], ["Sem 3", "21", "8.71", "Pass"], ["Sem 4", "22", "8.72", "Pass"]]}
        if slug == "marksheet-download":
            return {
                "description": "Complete internal and external marks summary with grade breakup.",
                "columns": ["Subject", "CAT 1", "CAT 2", "Assignment", "Total", "Grade"],
                "rows": [[row["subject"], row["cat1"], row["cat2"], row["assignment"], row["total"], row["grade"]] for row in STUDENT_MARKS],
            }
        if slug == "academic-history":
            return {"description": "Semester-wise academic history and status.", "columns": ["Semester", "Credits", "GPA", "Result"], "rows": [["Sem 1", "20", "8.51", "Pass"], ["Sem 2", "21", "8.64", "Pass"], ["Sem 3", "21", "8.71", "Pass"], ["Sem 4", "22", "8.72", "Pass"]]}
        if slug == "mentor-messages":
            return {"description": "Mentor communication and meeting records.", "columns": ["Date", "Mentor", "Message", "Status"], "rows": [["24 Jul", "Dr. Priya Nair", "Focus on CAT 2 preparation", "Read"], ["18 Jul", "Dr. Priya Nair", "Submit project abstract", "Read"], ["10 Jul", "Dr. Priya Nair", "Attend counseling hour", "Pending"]]}

    if role == "faculty":
        if slug == "faculty-profile":
            return {
                "description": "Faculty service details, workload, and department responsibilities.",
                "columns": ["Field", "Value", "Status", "Remark"],
                "rows": [
                    ["Faculty Name", "Dr. Priya Nair", "Verified", "Active staff"],
                    ["Employee ID", "PUFAC042", "Verified", "Permanent"],
                    ["Department", "Computer Science and Engineering", "Verified", "UG and PG teaching"],
                    ["Designation", "Associate Professor", "Verified", "Academic Council member"],
                    ["Subjects", "Web Dev, DBMS, Project Lab", "Assigned", "Current semester"],
                    ["Advisor Role", "Class Advisor - III CSE B", "Assigned", "Student guidance"],
                ],
            }
        if "attendance" in slug:
            return {
                "description": "Attendance operations for allocated classes and sections.",
                "columns": ["Time", "Subject", "Section", "Students"],
                "rows": [[time, subject, section, students] for time, subject, section, students in FACULTY_CLASSES],
            }
        if "cat-1" in slug:
            return {"description": "CAT 1 entry progress and pending list.", "columns": ["Subject", "Section", "Entered", "Pending"], "rows": [["Database Systems", "III CSE B", "42", "4"], ["Web Development", "III CSE A", "45", "3"], ["Software Engineering", "III CSE C", "41", "5"]]}
        if "cat-2" in slug:
            return {"description": "CAT 2 entry progress and pending list.", "columns": ["Subject", "Section", "Entered", "Pending"], "rows": [["Database Systems", "III CSE B", "40", "6"], ["Web Development", "III CSE A", "44", "4"], ["Software Engineering", "III CSE C", "39", "7"]]}
        if "assignment" in slug:
            return {"description": "Assignment evaluation and upload tracking.", "columns": ["Subject", "Submissions", "Evaluated", "Pending"], "rows": [["Database Systems", "46", "43", "3"], ["Web Development", "48", "46", "2"], ["Software Engineering", "44", "40", "4"]]}
        if "quiz" in slug:
            return {"description": "Quiz result entry and publication status.", "columns": ["Subject", "Attempts", "Published", "Pending"], "rows": [["Database Systems", "46", "Yes", "0"], ["Web Development", "47", "Yes", "0"], ["Software Engineering", "43", "No", "1"]]}
        if "lab" in slug or "practical" in slug:
            return {"description": "Lab and practical marks capture for all assigned batches.", "columns": ["Batch", "Subject", "Completed", "Pending"], "rows": [["III CSE A", "Web Lab", "22", "2"], ["III CSE B", "DB Lab", "21", "3"], ["IV CSE A", "Project Lab", "20", "4"]]}
        if "defaulter" in slug:
            return {"description": "Students below attendance threshold.", "columns": ["Reg No", "Name", "Attendance", "Action"], "rows": [["PU23CSE1889", "Nitin", "74%", "Notify"], ["PU23CSE1904", "Kavya", "73%", "Counseling"], ["PU23CSE1910", "Saran", "71%", "HOD alert"]]}
        if "reports" in slug or "summary" in slug:
            return {"description": "Department level faculty reports and analytics.", "columns": ["Report", "Prepared On", "Records", "Status"], "rows": [["CAT Performance", "25 Jul", "240", "Ready"], ["Attendance Summary", "25 Jul", "240", "Ready"], ["Outcome Attainment", "24 Jul", "18", "Draft"]]}

    if role == "admin":
        if slug == "admin-profile":
            return {
                "description": "Institution administration profile and operations ownership details.",
                "columns": ["Field", "Value", "Status", "Remark"],
                "rows": [
                    ["Admin Name", "System Administrator", "Verified", "Primary account"],
                    ["Employee ID", "PUADM001", "Verified", "Super admin"],
                    ["Control Scope", "University ERP", "Active", "All modules"],
                    ["Security Level", "Role-based", "Enabled", "Audit tracking active"],
                    ["Last Password Reset", "12 Jul 2026", "Compliant", "Within policy"],
                    ["Report Access", "PDF and Excel", "Enabled", "All departments"],
                ],
            }
        if slug == "student-master":
            return {
                "description": "Master list of students with enrollment and status details.",
                "columns": ["Reg No", "Name", "Department", "Status"],
                "rows": [["PU23CSE1842", "Prakash", "CSE", "Active"], ["PU23CSE1884", "Nisha Rao", "CSE", "Active"], ["PU23ECE1022", "Rahul Verma", "ECE", "Active"], ["PU23MEC0908", "Ishaan Patel", "MECH", "Probation"]],
            }
        if slug == "faculty-master":
            return {"description": "Faculty directory and designation mapping.", "columns": ["Employee ID", "Name", "Department", "Status"], "rows": [["PUFAC042", "Dr. Priya Nair", "CSE", "Active"], ["PUFAC018", "Dr. Meera", "ECE", "Active"], ["PUFAC065", "Dr. John", "MECH", "On Leave"]]}
        if "department" in slug or "program" in slug or "semester" in slug or "subject" in slug:
            return {"description": "Academic master settings and structures.", "columns": ["Master", "Count", "Updated", "Status"], "rows": [["Departments", "8", "24 Jul", "Active"], ["Programs", "18", "24 Jul", "Active"], ["Semesters", "16", "22 Jul", "Active"], ["Subjects", "324", "26 Jul", "Active"]]}
        if slug == "attendance-audit":
            return {"description": "Attendance audit consistency checks across departments.", "columns": ["Department", "Below 75%", "Corrected", "Status"], "rows": [["CSE", "18", "12", "Review"], ["ECE", "11", "8", "Review"], ["MECH", "14", "10", "Review"]]}
        if slug == "marks-audit":
            return {"description": "Internal and external marks validation status.", "columns": ["Department", "Records", "Mismatches", "Status"], "rows": [["CSE", "1240", "4", "Investigate"], ["ECE", "980", "2", "Investigate"], ["MECH", "860", "1", "Investigate"]]}
        if slug in {"gpa-audit", "cgpa-audit", "rank-list"}:
            return {"description": "Performance audit for GPA, CGPA, and rankings.", "columns": ["Batch", "Top GPA", "Average CGPA", "Validated"], "rows": [["2023 CSE", "9.41", "8.22", "Yes"], ["2023 ECE", "9.21", "8.11", "Yes"], ["2023 MECH", "8.94", "7.98", "Yes"]]}
        if "audit" in slug:
            return {
                "description": "Security and operations audit records across modules.",
                "columns": ["Time", "Actor", "Action", "Result"],
                "rows": [["09:02", "Admin", "Login", "Success"], ["09:14", "Faculty", "Marks Update", "Success"], ["10:06", "Student", "Transcript Download", "Success"], ["10:31", "System", "Backup", "Completed"]],
            }
        if "report" in slug:
            return {"description": "Report center queue and generation status.", "columns": ["Report", "Generated", "Format", "Status"], "rows": [["Department Report", "25 Jul", "PDF", "Ready"], ["Topper List", "25 Jul", "Excel", "Ready"], ["Attendance Defaulters", "26 Jul", "PDF", "Ready"]]}

    return default


def _build_module(role, title, index):
    now = datetime.now().strftime("%d %b %Y %I:%M %p")
    slug = _slugify(title)
    content = _module_content_for(role, slug, title, now)
    default_highlights = [
        f"Workflow checks enabled for {title}.",
        "Last sync completed without errors.",
        "Records validated against university policy.",
        "Export options are available for this module.",
    ]
    details = {
        "role": role,
        "slug": slug,
        "title": title,
        "description": content["description"],
        "status": "Active",
        "owner": "ERP Core Team",
        "updated_at": now,
        "stats": [
            {"label": "Records", "value": str(80 + (index * 7))},
            {"label": "Pending", "value": str((index % 5) + 1)},
            {"label": "Completed", "value": str(30 + (index * 3))},
            {"label": "Quality", "value": f"{90 + (index % 9)}%"},
        ],
        "highlights": content.get("highlights", default_highlights),
        "columns": content["columns"],
        "rows": content["rows"],
    }
    return details


def _modules_for_role(role):
    titles = {
        "student": STUDENT_MODULE_TITLES,
        "faculty": FACULTY_MODULE_TITLES,
        "admin": ADMIN_MODULE_TITLES,
    }[role]
    return [_build_module(role, title, idx + 1) for idx, title in enumerate(titles)]


MODULES_BY_ROLE = {
    "student": _modules_for_role("student"),
    "faculty": _modules_for_role("faculty"),
    "admin": _modules_for_role("admin"),
}


def _require_role(*roles):
    if current_user.role not in roles:
        return render_template("errors/403.html"), 403
    return None


def _role_allowed(requested_role):
    if current_user.role == "admin":
        return True
    return current_user.role == requested_role


def _find_module(role, slug):
    return next((item for item in MODULES_BY_ROLE[role] if item["slug"] == slug), None)


def _pdf_response(filename, title, rows):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(40, height - 50, "Student University")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(40, height - 68, title)
    pdf.setStrokeColor(colors.HexColor("#1f4e79"))
    pdf.line(40, height - 76, width - 40, height - 76)

    y = height - 110
    pdf.setFont("Helvetica-Bold", 10)
    for col_x, header in zip([40, 185, 305, 395, 485, 560], ["Subject", "CAT 1", "CAT 2", "Assign.", "Total", "Grade"]):
        pdf.drawString(col_x, y, header)

    pdf.setFont("Helvetica", 10)
    y -= 18
    for row in rows:
        values = [row["subject"], str(row["cat1"]), str(row["cat2"]), str(row["assignment"]), str(row["total"]), row["grade"]]
        for col_x, value in zip([40, 185, 305, 395, 485, 560], values):
            pdf.drawString(col_x, y, value)
        y -= 18
        if y < 70:
            pdf.showPage()
            y = height - 60

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


def _xlsx_response(filename, title, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Report"
    sheet.append(["Student University"])
    sheet.append([title])
    sheet.append([])
    sheet.append(["Subject", "CAT 1", "CAT 2", "Assignment", "Total", "Grade"])
    for row in rows:
        sheet.append([row["subject"], row["cat1"], row["cat2"], row["assignment"], row["total"], row["grade"]])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _module_book_pdf_response(module_no, module_book):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setTitle(module_book["title"])
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(40, height - 50, "Student University")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(40, height - 76, module_book["title"])
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, height - 94, f"Academic Module Booklet - Module {module_no}")
    pdf.setStrokeColor(colors.HexColor("#1f4e79"))
    pdf.line(40, height - 102, width - 40, height - 102)

    y = height - 128
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(40, y, "Key Topics")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for idx, topic in enumerate(module_book["topics"], start=1):
        pdf.drawString(48, y, f"{idx}. {topic}")
        y -= 16

    y -= 8
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(40, y, "Reference Books")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for idx, ref in enumerate(module_book["references"], start=1):
        pdf.drawString(48, y, f"{idx}. {ref}")
        y -= 16

    y -= 10
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(40, y, "Generated from Student University SARMS portal.")

    pdf.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"student-university-module-{module_no}-book.pdf",
        mimetype="application/pdf",
    )


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/student/dashboard")
@login_required
def student_dashboard():
    denied = _require_role("student", "admin")
    if denied:
        return denied

    modules = MODULES_BY_ROLE["student"]
    return render_template(
        "dashboards/student.html",
        marks=STUDENT_MARKS,
        attendance=STUDENT_ATTENDANCE,
        quick_modules=modules[:8],
        all_modules=modules,
        module_books=sorted(MODULE_BOOKS.items()),
    )


@main_bp.route("/faculty/dashboard")
@login_required
def faculty_dashboard():
    denied = _require_role("faculty", "admin")
    if denied:
        return denied

    modules = MODULES_BY_ROLE["faculty"]
    return render_template(
        "dashboards/faculty.html",
        classes_today=FACULTY_CLASSES,
        quick_modules=modules[:8],
        all_modules=modules,
    )


@main_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    denied = _require_role("admin")
    if denied:
        return denied

    modules = MODULES_BY_ROLE["admin"]
    return render_template("dashboards/admin.html", quick_modules=modules[:9], all_modules=modules)


@main_bp.route("/portal/<role>/<module_slug>")
@login_required
def module_detail(role, module_slug):
    if role not in MODULES_BY_ROLE:
        abort(404)
    if not _role_allowed(role):
        return render_template("errors/403.html"), 403

    module = _find_module(role, module_slug)
    if module is None:
        abort(404)

    if role == "admin" and module_slug == "audit-logs":
        valid, blocks = verify_academic_ledger()
        module = dict(module)
        module["ledger_valid"] = valid
        module["ledger_blocks"] = blocks

    return render_template("pages/module_detail.html", module=module, role=role)


@main_bp.route("/student/profile")
@login_required
def student_profile():
    return redirect(url_for("main.module_detail", role="student", module_slug="profile"))


@main_bp.route("/student/history")
@login_required
def student_history():
    return redirect(url_for("main.module_detail", role="student", module_slug="academic-history"))


@main_bp.route("/student/attendance")
@login_required
def student_attendance():
    return redirect(url_for("main.module_detail", role="student", module_slug="attendance-record"))


@main_bp.route("/faculty/attendance")
@login_required
def faculty_attendance():
    return redirect(url_for("main.module_detail", role="faculty", module_slug="attendance-entry"))


@main_bp.route("/faculty/marks")
@login_required
def faculty_marks():
    return redirect(url_for("main.module_detail", role="faculty", module_slug="cat-1-entry"))


@main_bp.route("/faculty/reports")
@login_required
def faculty_reports():
    return redirect(url_for("main.module_detail", role="faculty", module_slug="department-reports"))


@main_bp.route("/admin/students")
@login_required
def admin_students():
    return redirect(url_for("main.module_detail", role="admin", module_slug="student-master"))


@main_bp.route("/admin/faculty")
@login_required
def admin_faculty():
    return redirect(url_for("main.module_detail", role="admin", module_slug="faculty-master"))


@main_bp.route("/admin/audit")
@login_required
def admin_audit():
    return redirect(url_for("main.module_detail", role="admin", module_slug="audit-logs"))


@main_bp.route("/student/marksheet/pdf")
@login_required
def student_marksheet_pdf():
    denied = _require_role("student", "admin")
    if denied:
        return denied
    return _pdf_response("prakash-university-marksheet.pdf", "Student Marksheet", STUDENT_MARKS)


@main_bp.route("/student/marksheet/excel")
@login_required
def student_marksheet_excel():
    denied = _require_role("student", "admin")
    if denied:
        return denied
    return _xlsx_response("prakash-university-marksheet.xlsx", "Student Marksheet", STUDENT_MARKS)


@main_bp.route("/student/transcript/pdf")
@login_required
def student_transcript_pdf():
    denied = _require_role("student", "admin")
    if denied:
        return denied
    return _pdf_response("prakash-university-transcript.pdf", "Semester Transcript", STUDENT_MARKS)


@main_bp.route("/faculty/class-list/pdf")
@login_required
def faculty_class_list_pdf():
    denied = _require_role("faculty", "admin")
    if denied:
        return denied

    rows = [
        {
            "subject": subject,
            "cat1": time,
            "cat2": section,
            "assignment": students,
            "total": "",
            "grade": "",
        }
        for time, subject, section, students in FACULTY_CLASSES
    ]
    return _pdf_response("prakash-university-class-list.pdf", "Class Schedule", rows)


@main_bp.route("/admin/report/excel")
@login_required
def admin_report_excel():
    denied = _require_role("admin")
    if denied:
        return denied
    admin_rows = [
        {"subject": "Students", "cat1": 1248, "cat2": 0, "assignment": 0, "total": 1248, "grade": "Active"},
        {"subject": "Faculty", "cat1": 84, "cat2": 0, "assignment": 0, "total": 84, "grade": "Active"},
        {"subject": "Programs", "cat1": 18, "cat2": 0, "assignment": 0, "total": 18, "grade": "Active"},
    ]
    return _xlsx_response("prakash-university-institution-report.xlsx", "Institution Summary", admin_rows)


@main_bp.route("/student/module/<int:module_no>/download")
@login_required
def student_module_download(module_no):
    denied = _require_role("student", "admin")
    if denied:
        return denied

    module_book = MODULE_BOOKS.get(module_no)
    if module_book is None:
        abort(404)

    return _module_book_pdf_response(module_no, module_book)
