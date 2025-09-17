import os
from pathlib import Path
from dotenv import load_dotenv
from services.bot import GoogleGeminiInterviewBot
from services.evaluation import EvaluationService
from services.questionnaire import Questionnaire
from services.interview import InterviewService
from services.reporting import ReportService

import sounddevice as sd
from scipy.io.wavfile import write
import pygame


# --- Helper: Record from mic ---
def record_audio(filename: Path, duration=10, fs=16000):
    """
    Record audio from microphone and save as WAV.
    """
    print(f"🎙️ Recording for {duration} seconds... Speak now!")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()
    write(str(filename), fs, audio)  # Save as WAV
    print(f"✅ Saved recording to {filename}")


# --- Helper: Play audio file with pygame ---
def play_audio(filepath: Path):
    """
    Play an audio file (mp3 or wav) using pygame.
    """
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(str(filepath))
        pygame.mixer.music.play()

        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"⚠️ Could not play audio {filepath}: {e}")


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

    # Instantiate bot and interview service
    bot = GoogleGeminiInterviewBot(api_key=api_key, answer_bank=answer_bank)
    interview_service = InterviewService(bot=bot, answer_bank=answer_bank)

    # Candidate ID
    candidate_id = input("Enter candidate id: ")
    user_responses = []

    for idx, q in enumerate(questions_data, start=1):
        question_text = q["question_text"]
        topic_name = q["topic_name"]

        # --- Print question ---
        print(f"\nQ{idx} [{topic_name}]: {question_text}")

        # --- TTS: read question aloud ---
        tts_path = Path(f"question_{idx}.mp3")
        interview_service.bot.ask_question(question_text, tts_path)

        if tts_path.exists():
            play_audio(tts_path)  # 🔊 play question audio
        else:
            print("⚠️ No audio file generated for this question.")

        # --- Record user answer ---
        answer_audio_path = Path(f"answer_{idx}.wav")
        record_audio(answer_audio_path, duration=10)  # record 10 sec answer

        # --- STT: transcribe user answer ---
        user_answer = interview_service.bot.transcribe_answer(answer_audio_path)
        print(f"[STT] Transcribed answer: {user_answer}")

        # --- Compare with reference answer ---
        reference_answer = answer_bank[question_text]
        evaluation = interview_service.bot.evaluate_answer(user_answer, reference_answer)

        # --- Save response ---
        user_responses.append({
            "question_id": q["question_id"],
            "question_text": question_text,
            "topic_name": topic_name,
            "user_answer": user_answer,
            "correct_answer": reference_answer,
            "evaluation": evaluation
        })

        # --- Optional quit after 5 ---
        if idx >= 5:
            cont = input("Press Enter to continue or type 'q' to quit: ")
            if cont.lower() == "q":
                print("Exiting questionnaire...")
                break

    # Evaluate answers
    evaluation_service = EvaluationService()
    final_evaluation = evaluation_service.evaluate_answers(user_responses)

    # Display results
    print("\n\n📊 Questionnaire complete! Here are your results:")
    for result in final_evaluation["detailed_results"]:
        print(f"Question: {result['question_text']}")
        print(f"Your Answer: {result['user_answer']}")
        print(f"Correct Answer: {result['correct_answer']}")
        print(f"Score: {result['score']}/5\n")

    summary = final_evaluation["summary"]
    print(f"✨ Total Score: {summary['total_score']} out of {summary['max_possible_score']}")
    print(f"🌟 Average Score per Question: {summary['average_score_per_question']}/5")

    # Save report
    report_service = ReportService()
    report_service.generate_report(final_evaluation, file_format="json")


if __name__ == "__main__":
    main()
