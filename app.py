import uuid
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from services.bot import InterviewBotStrategy
from services.interview_runner import InterviewRunner 

AUDIO_DIR = Path("media/audio")
AUDIO_DIR.mkdir(exist_ok=True, parents=True)

app = FastAPI()

# In-memory store (replace with DB in production)
SESSIONS = {}

# ---------- Models ----------
class QuestionItem(BaseModel):
    question_id: str
    question_text: str
    tts_url: Optional[str] = None  # optional TTS URL

class StartInterviewRequest(BaseModel):
    candidate_id: str

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str

class DetailedResult(BaseModel):
    question_id: str
    question_text: str
    user_answer: str
    correct_answer: str
    topic_name: str
    score: int

class Summary(BaseModel):
    total_score: int
    max_possible_score: int
    average_score_per_question: float
    improvement_tips: List[str]

class SubmitAnswerResponse(BaseModel):
    message: str
    next_question: Optional[QuestionItem] = None
    detailed_results: Optional[List[DetailedResult]] = None
    summary: Optional[Summary] = None
class ReportResponse(BaseModel):
    session_id: str
    total_score: int
    weak_topics: list[str]

class StartInterviewResponse(BaseModel):
    session_id: str
    questions: list[QuestionItem]

q_limit = 1

# Load environment variables from .env
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ---------- API Endpoints ----------
@app.post("/start-interview", response_model=StartInterviewResponse)
async def start_interview(req: StartInterviewRequest):
    runner = InterviewRunner(req.candidate_id)
    session_id = str(uuid.uuid4())

    # Store session
    SESSIONS[session_id] = {"runner": runner, "answers": {}}

    questions = []
    for _, q in enumerate(runner.questions_data[:q_limit], start=1):
        speech_path = AUDIO_DIR / f"{session_id}_{q["question_id"]}.mp3"
        runner.bot.ask_question(q["question_text"], speech_path)
        questions.append(
            QuestionItem(
                question_id=q["question_id"],
                question_text=q["question_text"],
                tts_url=f"/media/audio/{speech_path.name}"
            )
        )

    return {"session_id": session_id, "questions": questions}

@app.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(req: SubmitAnswerRequest, q_limit: int = 1):
    """
    Submit an answer for a question.
    
    Args:
        req: SubmitAnswerRequest containing session_id, question_id, answer
        q_limit: optional number of questions to evaluate before finishing
    """
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not req.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty")

    runner: InterviewRunner = session["runner"]

    # Set default question limit to all questions if not provided
    if q_limit is None:
        q_limit = len(runner.questions_data)

    # Validate question_id format
    if not req.question_id.startswith("q") or not req.question_id[1:].isdigit():
        raise HTTPException(status_code=400, detail="Invalid question_id format")

    # Ensure question exists and within limit
    all_question_ids = [q["question_id"] for q in runner.questions_data[:q_limit]]
    if req.question_id not in all_question_ids:
        raise HTTPException(status_code=400, detail="Invalid question_id")

    # Store answer
    session["answers"][req.question_id] = req.answer

    # Determine remaining questions
    answered_ids = list(session["answers"].keys())
    remaining_ids = [qid for qid in all_question_ids if qid not in answered_ids]

    if not remaining_ids:
        # All questions answered → calculate final score and return detailed results
        try:
            results = runner.run_api(session["answers"])
            
            # Check if evaluation failed due to rate limit
            if any(result.get("score") == -1 for result in results.get("detailed_results", [])):
                session["score"] = 0
                session["weak_topics"] = []
                return SubmitAnswerResponse(
                    message="Interview complete! However, we've reached our daily evaluation limit. Your answers have been saved, but scoring is temporarily unavailable. Please try again later for detailed feedback.",
                    detailed_results=None,
                    summary=Summary(
                        total_score=0,
                        max_possible_score=len(session["answers"]) * 5,
                        average_score_per_question=0.0,
                        improvement_tips=["Evaluation temporarily unavailable due to rate limits. Please try again later."]
                    )
                )
            
            session["score"] = results["summary"]["total_score"]
            session["weak_topics"] = results.get("weak_topics", [])
            
            # Return the complete detailed results
            return SubmitAnswerResponse(
                message=f"Answer recorded. Interview complete! Total score: {results['summary']['total_score']}",
                detailed_results=results["detailed_results"],
                summary=results["summary"]
            )
            
        except Exception as e:
            # Handle any other errors during evaluation
            print(f"Error during evaluation: {e}")
            
            # Check if it's specifically a rate limit error
            if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                return SubmitAnswerResponse(
                    message="Interview complete! However, we've reached our daily evaluation limit. Your answers have been saved, but scoring is temporarily unavailable. Please try again in a few hours for detailed feedback."
                )
            else:
                # Generic error fallback
                return SubmitAnswerResponse(
                    message="Interview complete! Your answers have been saved, but there was an issue with evaluation. Please try again later."
                )

    # Otherwise, return next question
    next_q_id = remaining_ids[0]
    next_q_data = next(q for q in runner.questions_data if q["question_id"] == next_q_id)

    tts_file = AUDIO_DIR / f"{req.session_id}_question_{next_q_id}.mp3"
    if not tts_file.exists():
        runner.bot.ask_question(next_q_data["question_text"], tts_file)

    next_question = QuestionItem(
        question_id=next_q_id,
        question_text=next_q_data["question_text"],
        tts_url=f"/media/audio/{tts_file.name}"
    )

    return SubmitAnswerResponse(
        message="Answer recorded.",
        next_question=next_question
    )

@app.get("/get-report/{session_id}", response_model=ReportResponse)
async def get_report(session_id: str):
    """TC-05, TC-06 Fetch final report."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Report not found")

    runner: InterviewRunner = session["runner"]
    answers = session["answers"]

    try:
        results = runner.run_api(answers)
        return {
            "session_id": session_id,
            "total_score": results["total_score"],
            "weak_topics": results.get("weak_topics", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
