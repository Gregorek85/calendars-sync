from bs4 import BeautifulSoup


def clean_subject(subject):
    # remove prefix clutter from an outlook event subject
    remove = [
        "Fwd: ",
        "Invitation: ",
        "Updated invitation: ",
        "Updated invitation with note: ",
    ]
    for s in remove:
        subject = subject.replace(s, "")
    return subject


def clean_body(no):
    return f"Wydarzenie z pracy Radka, liczba uczestników: {no}"
