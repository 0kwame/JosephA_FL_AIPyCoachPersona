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
        results = {}

        for i, question in enumerate(questions, start=1):
            print(f"\nQ{i}: {question}")

            # TTS
            speech_path = Path(f"question_{i}.mp3")
            self.bot.ask_question(question, speech_path)

            # STT (assuming audio file already recorded)
            audio_path = Path(f"answer_{i}.mp3")
            user_answer = self.bot.transcribe_answer(audio_path)

            # Compare with reference
            reference_answer = self.answer_bank.get(question, "")
            evaluation = self.bot.evaluate_answer(user_answer, reference_answer)

            results[question] = evaluation

        print("\nInterview completed.")
        return {
            "candidate_id": candidate_id,
            "results": results
        }
