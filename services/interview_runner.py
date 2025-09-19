import os
from pathlib import Path
from services.bot import GoogleGeminiInterviewBot, GeminiEvaluator
from services.evaluation import GeminiEvaluationStrategy
from services.questionnaire import Questionnaire
from services.interview import InterviewService
from services.reporting import ReportService

class InterviewRunner:
    def __init__(self, candidate_id: str):
        self.candidate_id = candidate_id

        # Load questions
        questionnaire = Questionnaire()
        self.questions_data = questionnaire.get_all_questions()
        self.answer_bank = {q["question_text"]: q["answer_text"] for q in self.questions_data}

        # Bot setup with strategy
        api_key = os.getenv("PROVIDER_API_KEY")
        if not api_key:
            raise ValueError("PROVIDER_API_KEY not set")

        gemini_evaluator = GeminiEvaluator(api_key=api_key)

        gemini_strategy = GeminiEvaluationStrategy(
            gemini_evaluator=gemini_evaluator,
            answer_bank=self.answer_bank
        )

        self.bot = GoogleGeminiInterviewBot(
            evaluation_strategy=gemini_strategy,
            answer_bank=self.answer_bank
        )

        # Services
        self.interview_service = InterviewService(bot=self.bot, answer_bank=self.answer_bank)
        self.report_service = ReportService()

    def run_cli(self, q_limit: int = 1):
        """Run the interview interactively in terminal."""
        from audio import AudioService  # only needed in CLI

        audio = AudioService()
        user_responses = []

        # Determine limit
        if q_limit is None or q_limit > len(self.questions_data):
            q_limit = len(self.questions_data)

        limited_questions = self.questions_data[:q_limit]

        for idx, q in enumerate(limited_questions, start=1):
            question_text = q["question_text"]
            topic_name = q.get("topic_name", "Unknown Topic")

            print(f"\nQ{idx} [{topic_name}]: {question_text}")

            # --- TTS ---
            tts_path = Path(f"media/audio/{self.candidate_id}_q{idx}.mp3")
            self.bot.ask_question(question_text, tts_path)
            if tts_path.exists():
                audio.play(tts_path)

            # --- Record answer ---
            ans_path = Path(f"media/audio/{self.candidate_id}_a{idx}.wav")
            audio.record(ans_path, duration=10)
            user_answer = self.bot.transcribe_answer(ans_path)

            # --- Build response ---
            response = {
                "question_id": q.get("question_id", f"q{idx}"),
                "question_text": question_text,
                "topic_name": topic_name,
                "user_answer": user_answer,
                "correct_answer": self.answer_bank[question_text],
            }
            user_responses.append(response)

        # After the loop, evaluate in batch
        evaluated = self.bot.evaluate_answers(user_responses)
        return self._finalize(evaluated)

    def run_api(self, user_answers: dict, q_limit: int = 1):
        """
        Run the interview with answers provided (uploaded or text),
        evaluate only the first `q_limit` questions as a single batch,
        and return full report.
        """
        user_responses = []

        # Determine limit
        if q_limit is None or q_limit > len(self.questions_data):
            q_limit = len(self.questions_data)

        # Build the list of responses for only the limited set
        limited_questions = self.questions_data[:q_limit]

        for idx, q in enumerate(limited_questions, start=1):
            question_text = q["question_text"]
            topic_name = q.get("topic_name", "Unknown Topic")
            user_answer = user_answers.get(q["question_id"], "")
            reference_answer = self.answer_bank.get(question_text, "")

            user_responses.append({
                "question_id": q["question_id"],  # keep original question_id
                "question_text": question_text,
                "user_answer": user_answer,
                "correct_answer": reference_answer,
                "topic_name": topic_name
            })

        # Evaluate all answers at once
        evaluations = self.bot.evaluate_answers(user_responses)

        # Merge evaluation results into user_responses
        total_score = 0
        max_score_per_question = 5
        for resp, eval_res in zip(user_responses, evaluations):
            score = eval_res.get("score", 0)
            resp["score"] = score
            total_score += score

        report = {
            "detailed_results": user_responses,
            "summary": {
                "total_score": total_score,
                "max_possible_score": len(user_responses) * max_score_per_question,
                "average_score_per_question": total_score / len(user_responses) if user_responses else 0,
                "improvement_tips": []  # can be filled from evaluation explanations if desired
            }
        }

        # Save report if needed
        self.report_service.generate_report(report, file_format="json")
        return report


    def _finalize(self, responses: list) -> dict:
        # Get list of evaluated responses
        evaluated_responses = self.bot.strategy.evaluate_answers(responses)

        # Build summary
        total_score = sum(resp.get("score", 0) for resp in evaluated_responses)
        max_score_per_question = 5
        report = {
            "detailed_results": evaluated_responses,
            "summary": {
                "total_score": total_score,
                "max_possible_score": len(evaluated_responses) * max_score_per_question,
                "average_score_per_question": total_score / len(evaluated_responses) if evaluated_responses else 0,
                "improvement_tips": []  # optionally fill from evaluation explanations
            }
        }

        self.report_service.generate_report(report, file_format="json")
        return report


