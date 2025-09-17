import random
from typing import List, Dict, Any
from repository import QuestionRepository
from services.evaluation import EvaluationService
from services.reporting import ReportService # Assuming you save the above class here

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


def run_questionnaire(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    random.shuffle(questions)
    user_responses = []

    print("📝 Starting the questionnaire. Your answers will be evaluated at the end.")
    print("----------------------------------------------------------------------")

    for idx, q in enumerate(questions, start=1):
        print(f"Q{idx} [{q['topic_name']}]: {q['question_text']}")
        answer = input("Your answer: ")

        user_responses.append({
            "question_id": q["question_id"],
            "question_text": q["question_text"],
            "topic_name": q["topic_name"],  # Add topic name for the report
            "user_answer": answer,
            "correct_answer": q["answer_text"]
        })

        print("✅ Answer recorded.\n")

        if idx >= 5:
            cont = input("Press Enter to continue or type 'q' to quit: ")
            if cont.lower() == "q":
                print("Exiting questionnaire...")
                break

    # 1. Evaluate all answers using the EvaluationService
    print("\n\n📊 Questionnaire complete! Here are your results:")
    print("---------------------------------------------------")
    
    evaluation_service = EvaluationService()
    final_evaluation = evaluation_service.evaluate_answers(user_responses)

    # 2. Display the detailed and summary results
    for result in final_evaluation["detailed_results"]:
        print(f"Question: {result['question_text']}")
        print(f"Your Answer: {result['user_answer']}")
        print(f"Correct Answer: {result['correct_answer']}")
        print(f"Score: {result['score']}/5\n")
    
    summary = final_evaluation["summary"]
    print(f"✨ Total Score: {summary['total_score']} out of {summary['max_possible_score']}")
    print(f"🌟 Average Score per Question: {summary['average_score_per_question']}/5")
    
    # 3. Save the report using the ReportService
    report_service = ReportService()
    report_service.generate_report(final_evaluation, file_format="json")

    return user_responses


if __name__ == "__main__":
    print("Loading questions from the repository...\n")
    questionnaire = Questionnaire()
    questions = questionnaire.get_all_questions()
    run_questionnaire(questions)
