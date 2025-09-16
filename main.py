import random
from repository import QuestionRepository

# -------------------------------
# Helper function: Levenshtein distance
# -------------------------------
def levenshtein_distance(s1, s2):
    len_s1, len_s2 = len(s1), len(s2)
    dp = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]

    for i in range(len_s1 + 1):
        dp[i][0] = i
    for j in range(len_s2 + 1):
        dp[0][j] = j

    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            if s1[i - 1].lower() == s2[j - 1].lower():
                cost = 0
            else:
                cost = 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )

    return dp[len_s1][len_s2]

def calculate_score(user_answer, correct_answer):
    distance = levenshtein_distance(user_answer, correct_answer)
    length = max(len(correct_answer), 1)  # avoid division by zero
    normalized_distance = distance / length

    if normalized_distance == 0:
        return 5
    elif normalized_distance <= 0.2:
        return 4
    elif normalized_distance <= 0.4:
        return 3
    elif normalized_distance <= 0.6:
        return 2
    elif normalized_distance <= 0.8:
        return 1
    else:
        return 0



class Questionnaire:
    def __init__(self):
        self.question_repo = QuestionRepository()

    def get_all_questions(self):
        dataset = self.question_repo.questions
        all_questions = []

        # Flatten nested topics → qa_pairs
        for topic in dataset.get("topics", []):
            topic_id = topic.get("topic_id", "UnknownTopic")
            topic_name = topic.get("topic", "Unknown Topic")

            for qa in topic.get("qa_pairs", []):
                q_id = qa.get("question_id", "UnknownID")
                q_text = qa.get("question", "No question text available")
                a_id = qa.get("answer_id", "UnknownAnswer")
                a_text = qa.get("answer", "No answer available")

                all_questions.append({
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "question_id": q_id,
                    "question_text": q_text,
                    "answer_id": a_id,
                    "answer_text": a_text
                })

        return all_questions


def run_questionnaire(questions):
    # Shuffle randomly
    random.shuffle(questions)
    answers = []

    for idx, q in enumerate(questions, start=1):
        print(f"Q{idx} [{q['topic_name']}]: {q['question_text']}")
        answer = input("Your answer: ")

        # Compute Levenshtein distance
        distance = calculate_score(answer, q["answer_text"])

        answers.append({
            "question_id": q["question_id"],
            "question_text": q["question_text"],
            "user_answer": answer,
            "correct_answer": q["answer_text"],
            "levenshtein_distance": distance
        })

        print(f"✅ Recorded your answer: {answer}")
        print(f"📏 Distance from correct answer: {distance}\n")

        # Stop after at least 5 questions if user quits
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
