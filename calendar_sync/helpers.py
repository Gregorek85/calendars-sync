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


def clean_body(body):
    # TODO
    # strip out html and excess line returns from outlook event body
    text = BeautifulSoup(body, "html.parser").get_text()
    return text.replace("\n", " ").replace("\r", "\n")