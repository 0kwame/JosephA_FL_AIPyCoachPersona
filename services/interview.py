from pathlib import Path
from services.bot import InterviewBotStrategy

class InterviewService:
    """
    Service to conduct interviews using an AI strategy.
    """

    def __init__(self, bot: InterviewBotStrategy, answer_bank: dict):
        self.bot = bot
        self.answer_bank = answer_bank

    def conduct_interview(self, candidate_id: str, questions: list) -> dict:
        print(f"Starting interview with {candidate_id}...")
        responses = []

        for i, question in enumerate(questions, start=1):
            print(f"\nQ{i}: {question}")

            # --- TTS ---
            speech_path = Path(f"question_{i}.mp3")
            self.bot.ask_question(question, speech_path)

            # --- STT (assuming audio file already recorded) ---
            audio_path = Path(f"answer_{i}.mp3")
            user_answer = self.bot.transcribe_answer(audio_path)

            # --- Build structured response ---
            responses.append({
                "question_id": f"q{i}",
                "question_text": question,
                "user_answer": user_answer,
                "correct_answer": self.answer_bank.get(question, ""),
            })

        # --- Batch evaluate ---
        evaluated = self.bot.evaluate_answers(responses)

        print("\nInterview completed.")
        return {
            "candidate_id": candidate_id,
            "results": evaluated
        }
