import random
from repository import QuestionRepository

class Questionnaire:
    def __init__(self):
        self.question_repo = QuestionRepository()

    def get_all_questions(self):
        return self.question_repo.questions


def run_questionnaire(questions):
    # Flatten all questions with their topics
    all_questions = []
    for section in questions:
        topic = section.get("topic", "Unknown Topic")
        for q in section.get("questions", []):
            all_questions.append((topic, q))

    # Shuffle questions randomly
    random.shuffle(all_questions)
    answers = []

    for idx, (topic, question) in enumerate(all_questions, start=1):
        print(f"Q{idx} ({topic}): {question}")
        answer = input("Your answer: ")
        answers.append({"question": question, "topic": topic, "answer": answer})

        print(f"✅ Recorded your answer: {answer}\n")

        # Enforce minimum of 5 before quitting
        if idx >= 5:
            cont = input("Press Enter to continue or type 'q' to quit: ")
            if cont.lower() == "q":
                print("Exiting questionnaire...")
                break

    return answers


if __name__ == "__main__":
    print("Loading questions from the repository...\n")
    questionnaire = Questionnaire()
    questions = questionnaire.get_all_questions()
    run_questionnaire(questions)
