
from repository.questions import QuestionRepository


class Questionnaire:
    def __init__(self):
        self.question_repo = QuestionRepository()

    def get_all_questions(self):
        topics = self.question_repo.questions
        all_questions = []

        for topic in topics:
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

