from datetime import date
from xml.sax.saxutils import escape


def snapshot(internship):
    student = internship.student
    profile = getattr(student, 'profile', None)
    return {
        'student_name': student.full_name,
        'gender': profile.gender if profile else 'MALE',
        'candidate_type': getattr(profile, 'candidate_type', 'COLLEGE_INTERN') if profile else 'COLLEGE_INTERN',
        'institution_name': profile.college_name if profile else '',
        'department': profile.department if profile else '',
        'course': profile.course if profile else '',
        'register_number': profile.register_number if profile else '',
        'project_name': internship.project_name,
        'start_date': internship.start_date.isoformat(),
        'end_date': internship.end_date.isoformat() if internship.end_date else None,
    }


def paragraphs(data):
    female = data['gender'] == 'FEMALE'
    title, subject, obj, possessive = ('Ms.', 'she', 'her', 'her') if female else ('Mr.', 'he', 'him', 'his')
    name = f"<b>{title} {escape(data['student_name'])}</b>"
    project = escape(data['project_name'])
    start = date.fromisoformat(data['start_date']).strftime('%d/%m/%Y')
    end = date.fromisoformat(data['end_date']).strftime('%d/%m/%Y')
    return [
        f'This is to certify that {name} has completed {possessive} internship in our organization from <b>{start} to {end}</b>.',
        f'Throughout the period, {name} displayed exceptional dedication and a strong sense of responsibility, making {obj} an invaluable candidate of our project <b>“{project}”</b>.',
        f'We have no doubt that {name} will continue to excel in {possessive} future endeavours. {possessive.capitalize()} strong dedication towards continuous growth and improvement will undoubtedly lead to great success.',
        f'We wish {obj} all the best in {possessive} future career, and we are confident that {subject} will continue to make a positive impact in any role {subject} undertakes.',
    ]
