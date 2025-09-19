from pathlib import Path
import os
from dotenv import load_dotenv
from services.questionnaire import Questionnaire
from services.reporting import ReportService
from services.audio import AudioService
from services.bot import GoogleGeminiInterviewBot, GeminiEvaluator
from services.evaluation import GeminiEvaluationStrategy


def main():
    # Load environment variables from .env
    load_dotenv(dotenv_path=Path(__file__).parent / ".env")

    print("Loading questions from the repository...\n")
    questionnaire = Questionnaire()
    questions_data = questionnaire.get_all_questions()

    # Build the answer bank from questions
    answer_bank = {q["question_text"]: q["answer_text"] for q in questions_data}

    # Get the API key
    api_key = os.getenv("PROVIDER_API_KEY")
    if api_key is None:
        raise ValueError("PROVIDER_API_KEY is not set in the environment.")

    # Instantiate Gemini evaluator & strategy
    gemini_evaluator = GeminiEvaluator(api_key=api_key)
    gemini_strategy = GeminiEvaluationStrategy(
        gemini_evaluator=gemini_evaluator,
        answer_bank=answer_bank
    )

    # Instantiate bot with evaluation strategy
    bot = GoogleGeminiInterviewBot(
        evaluation_strategy=gemini_strategy,
        answer_bank=answer_bank
    )

    # Instantiate services
    report_service = ReportService()
    audio = AudioService()

    # Ensure audio directory exists
    AUDIO_DIR = Path("media/audio")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Candidate ID
    candidate_id = input("Enter candidate id: ").strip()
    user_responses = []

    for idx, q in enumerate(questions_data, start=1):
        question_text = q["question_text"]
        topic_name = q.get("topic_name", "Unknown Topic")

        # --- Print question ---
        print(f"\nQ{idx} [{topic_name}]: {question_text}")

        # --- TTS: read question aloud ---
        tts_path = AUDIO_DIR / f"{candidate_id}_question_{idx}.mp3"
        bot.ask_question(question_text, tts_path)

        if tts_path.exists():
            audio.play(tts_path)
        else:
            print("⚠️ No audio file generated for this question.")

        # --- Record user answer ---
        answer_audio_path = AUDIO_DIR / f"{candidate_id}_answer_{idx}.wav"
        audio.record(answer_audio_path, duration=10)

        # --- STT: transcribe user answer ---
        user_answer = bot.transcribe_answer(answer_audio_path)
        print(f"[STT] Transcribed answer: {user_answer}")

        # --- Build response (NO per-question evaluation here) ---
        user_responses.append({
            "question_id": q["question_id"],
            "question_text": question_text,
            "topic_name": topic_name,
            "user_answer": user_answer,
            "correct_answer": answer_bank[question_text],
        })

        # Optional quit after 5 questions
        if idx >= 5:
            cont = input("Press Enter to continue or type 'q' to quit: ")
            if cont.lower() == "q":
                print("Exiting questionnaire...")
                break

    # --- Batch evaluation ---
    final_evaluation = bot.evaluate_answers(user_responses)

    # Build report with summary
    total_score = sum(r.get("score", 0) for r in final_evaluation)
    max_score_per_question = 5
    report = {
        "detailed_results": final_evaluation,
        "summary": {
            "total_score": total_score,
            "max_possible_score": len(final_evaluation) * max_score_per_question,
            "average_score_per_question": total_score / len(final_evaluation) if final_evaluation else 0,
            "improvement_tips": []  # optionally add explanation tips
        }
    }

    # Display results
    print("\n\n📊 Questionnaire complete! Here are your results:")
    for result in report["detailed_results"]:
        print(f"Question: {result['question_text']}")
        print(f"Your Answer: {result['user_answer']}")
        print(f"Correct Answer: {result['correct_answer']}")
        print(f"Score: {result['score']}/5\n")

    summary = report["summary"]
    print(f"✨ Total Score: {summary['total_score']} out of {summary['max_possible_score']}")
    print(f"🌟 Average Score per Question: {summary['average_score_per_question']}/5")

    # Save report
    report_service.generate_report(report, file_format="json")


if __name__ == "__main__":
    main()
