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
        for question in section.get("questions", []):
            all_questions.append((topic, question))

    # Shuffle questions randomly
    random.shuffle(all_questions)
    answers = []

    for idx, (topic, question) in enumerate(all_questions, start=1):
        print(f"Q{idx} ({topic}): {question}")

        # Require a non-empty answer (reprompt if user just presses Enter)
        while True:
            answer = input("Your answer: ")
            if answer.strip():
                break
            print("Please provide an answer (cannot be empty).")

        answers.append({"question": question, "topic": topic, "answer": answer})

        print(f"✅ Recorded your answer: {answer}\n")

        # Enforce minimum of 5 before quitting
        if idx >= 5:
            continue_response = input("Press Enter to continue or type 'q' to quit: ")
            if continue_response.lower() == "q":
                print("Exiting questionnaire...")
                break

    return answers

def main():
    print("Loading questions from the repository...\n")
    questionnaire = Questionnaire()
    questions = questionnaire.get_all_questions()
    run_questionnaire(questions)


if __name__ == "__main__":
    main()
