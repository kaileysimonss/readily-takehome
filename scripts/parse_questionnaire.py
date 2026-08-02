import json
import os

from lib.questionnaire_pdf import extract_questions

FILE = os.path.join(
    os.path.dirname(__file__), "..", "docs", "Public Policies", "Regulatory Questionnaire.pdf"
)
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "questionnaire", "questions.json")
DOC = "Regulatory Questionnaire"
DOC_TITLE = "DHCS Submission Review Form - APL 25-008 (Hospice Services and Medi-Cal Managed Care)"


def main():
    questions = extract_questions(FILE)

    out = [
        {
            "questionId": f"SRF-Q{q['number']}",
            "doc": DOC,
            "docTitle": DOC_TITLE,
            "page": q["page"],
            "number": q["number"],
            "question": q["text"],
            "reference": q["reference"],
        }
        for q in questions
    ]

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w") as f:
        json.dump(out, f, indent=2)

    print(f"Parsed {len(out)} questions -> {OUT_FILE}")


if __name__ == "__main__":
    main()
