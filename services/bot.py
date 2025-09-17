from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
import google.generativeai as genai
from google.cloud import texttospeech, speech


# --- Strategy Interface ---
class InterviewBotStrategy(ABC):
    """
    Abstract strategy for interview bots.
    """

    @abstractmethod
    def ask_question(self, question: str, speech_file_path: Path):
        """Read the question out loud using TTS."""
        pass

    @abstractmethod
    def transcribe_answer(self, audio_file_path: Path) -> str:
        """Convert candidate speech to text using STT."""
        pass

    @abstractmethod
    def evaluate_answer(self, user_answer: str, reference_answer: str) -> dict:
        """Compare the user's answer to the reference answer."""
        pass


# --- Hidden Services ---
class GoogleTTSService:
    def __init__(self):
        # 1. Check if JSON key is provided via env var (base64 or raw JSON)
        if "GCP_TTS_KEY" in os.environ:
            try:
                key_data = os.environ["GCP_TTS_KEY"]
                # Support both raw JSON and base64-encoded
                if key_data.strip().startswith("{"):
                    creds_json = json.loads(key_data)
                else:
                    import base64
                    creds_json = json.loads(base64.b64decode(key_data))
                self.client = texttospeech.TextToSpeechClient.from_service_account_info(creds_json)
                return
            except Exception as e:
                print(f"[WARN] Failed to load GCP_TTS_KEY: {e}")

        # 2. Fallback: use local JSON file
        local_key = Path(__file__).parent.parent / "keys" / "tts.json"
        if local_key.exists():
            self.client = texttospeech.TextToSpeechClient.from_service_account_file(str(local_key))
            return

        # 3. Last resort: Application Default Credentials (ADC)
        self.client = texttospeech.TextToSpeechClient()

    def synthesize(self, text: str, file_path: Path):
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        file_path.write_bytes(response.audio_content)

class GoogleSTTService:
    def __init__(self):
        # 1. Check env var
        if "GCP_STT_KEY" in os.environ:
            try:
                key_data = os.environ["GCP_STT_KEY"]
                if key_data.strip().startswith("{"):
                    creds_json = json.loads(key_data)
                else:
                    import base64
                    creds_json = json.loads(base64.b64decode(key_data))
                self.client = speech.SpeechClient.from_service_account_info(creds_json)
                return
            except Exception as e:
                print(f"[WARN] Failed to load GCP_STT_KEY: {e}")

        # 2. Fallback: local JSON
        local_key = Path(__file__).parent.parent / "keys" / "stt.json"
        if local_key.exists():
            self.client = speech.SpeechClient.from_service_account_file(str(local_key))
            return

        # 3. Fallback: ADC
        self.client = speech.SpeechClient()

    def transcribe(self, audio_file_path: Path) -> str:
        """Transcribe audio into text"""
        with audio_file_path.open("rb") as f:
            audio = speech.RecognitionAudio(content=f.read())

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,  # Adjust if different
            sample_rate_hertz=16000,  # Adjust if different
            language_code="en-US",
        )

        response = self.client.recognize(config=config, audio=audio)

        return " ".join([result.alternatives[0].transcript for result in response.results])



class GeminiEvaluator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key) # type: ignore
        self.model = genai.GenerativeModel("gemini-1.5-flash") # type: ignore

    def evaluate(self, user_answer: str, reference_answer: str) -> dict:
        prompt = f"""
        Compare the following candidate answer to the reference.
        Candidate: {user_answer}
        Reference: {reference_answer}
        Give a score (1-5) and a short explanation.
        """
        response = self.model.generate_content(prompt)
        return {"evaluation": response.text}


# --- Google/Gemini Strategy ---
class GoogleGeminiInterviewBot(InterviewBotStrategy):
    def __init__(self, api_key: str, answer_bank: dict):
        self.tts = GoogleTTSService()
        self.stt = GoogleSTTService()
        self.evaluator = GeminiEvaluator(api_key)
        self.answer_bank = answer_bank

    def ask_question(self, question: str, speech_file_path: Path):
        self.tts.synthesize(question, speech_file_path)

    def transcribe_answer(self, audio_file_path: Path) -> str:
        return self.stt.transcribe(audio_file_path)

    def evaluate_answer(self, user_answer: str, reference_answer: str) -> dict:
        return self.evaluator.evaluate(user_answer, reference_answer)

    def conduct_interview(self, candidate_id: str, questions: list) -> dict:
        print(f"Starting Google/Gemini interview with {candidate_id}...")
        results = {}

        for i, question in enumerate(questions, start=1):
            print(f"\nQ{i}: {question}")

            # Ask
            speech_path = Path(f"question_{i}.mp3")
            self.ask_question(question, speech_path)

            # Transcribe
            audio_path = Path(f"answer_{i}.wav")  # recorded answer
            user_answer = self.transcribe_answer(audio_path)

            # Evaluate
            reference_answer = self.answer_bank.get(question, "")
            evaluation = self.evaluate_answer(user_answer, reference_answer)

            results[question] = evaluation

        print("\nInterview completed.")
        return {"candidate_id": candidate_id, "results": results}
