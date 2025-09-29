from abc import ABC, abstractmethod
import json
from typing import List, Dict, Any
import Levenshtein

# -----------------------------
# Abstract Evaluation Strategy
# -----------------------------
class EvaluationServiceStrategy(ABC):
    """
    Abstract base class for evaluation strategies.
    Concrete implementations must implement `evaluate_answers`.
    """

    @abstractmethod
    def evaluate_answers(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate one or more answers.
        Each response dict must contain at least:
        {
            "user_answer": str,
            "correct_answer": str,
            ...
        }
        Returns a list of responses with 'score' and 'evaluation' added.
        """
        pass

# -----------------------------
# Levenshtein-based Strategy
# -----------------------------
class LevenshteinStrategy(EvaluationServiceStrategy):
    """
    Evaluates answers based on normalized Levenshtein distance.
    """

    def _calculate_score(self, user_answer: str, correct_answer: str) -> int:
        distance = Levenshtein.distance(user_answer.lower(), correct_answer.lower())
        length = max(len(correct_answer), 1)
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

    # def evaluate_answer(self, user_answer: str, correct_answer: str) -> Dict[str, Any]:
    #     score = self._calculate_score(user_answer, correct_answer)
    #     evaluation_text = f"Levenshtein distance-based score: {score}"
    #     return {"score": score, "evaluation": evaluation_text}
    
    def evaluate_answers(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate one or more responses.
        Each response dict should contain:
        {
            "user_answer": str,
            "correct_answer": str,
            ...
        }
        Returns list of responses with added 'score' and 'evaluation'.
        """
        evaluated_responses = []

        for resp in responses:
            score = self._calculate_score(resp["user_answer"], resp["correct_answer"])
            evaluation_text = f"Levenshtein distance-based score: {score}"

            new_resp = resp.copy()
            new_resp["score"] = score
            new_resp["evaluation"] = evaluation_text
            evaluated_responses.append(new_resp)

        return evaluated_responses

# -----------------------------
# Gemini / Google LLM Strategy
# -----------------------------
class GeminiEvaluationStrategy(EvaluationServiceStrategy):
    """
    Uses a Gemini model to evaluate answers (LLM-based scoring).
    """

    def __init__(self, gemini_evaluator, answer_bank: dict):
        self.evaluator = gemini_evaluator
        self.answer_bank = answer_bank
        self.fallback_strategy = LevenshteinStrategy()  # fallback

    def evaluate_answers(self, responses: list) -> list:
            """
            Try Gemini batch evaluation. If it fails, fallback to Levenshtein.
            """
            response_text = "N/A"
            
            # Build batch prompt
            batch_prompt = "Compare the following candidate answers to the reference answers:\n\n"
            for resp in responses:
                batch_prompt += f"Question: {resp['question_text']}\n"
                batch_prompt += f"Candidate: {resp['user_answer']}\n"
                batch_prompt += f"Reference: {resp['correct_answer']}\n\n"

            batch_prompt += (
                "For each answer, provide a numeric score (1-5) and a short explanation. "
                "Return the results as a JSON list in the following format:\n"
                "[{'question_id': 'q1', 'score': 4, 'evaluation': 'short explanation', "
                "'topic_name': '...'}, ...]"
            )

            try:
                response = self.evaluator.model.generate_content(batch_prompt)
                response_text = response.text.strip()

                # --- Extract JSON safely ---
                if response_text.startswith('```json'):
                    start_idx = response_text.find('```json') + len('```json')
                    end_idx = response_text.find('```', start_idx)
                    json_content = response_text[start_idx:end_idx].strip() if end_idx != -1 else response_text[start_idx:].strip()
                elif response_text.startswith('```'):
                    lines = response_text.split('\n')
                    json_content = '\n'.join(lines[1:-1])
                else:
                    json_content = response_text

                evaluations_raw = json.loads(json_content)
                eval_map = {e["question_id"]: e for e in evaluations_raw}

                # Merge back into responses
                evaluated_responses = []
                for resp in responses:
                    eval_entry = eval_map.get(resp["question_id"])
                    if eval_entry:
                        new_resp = resp.copy()
                        new_resp["score"] = eval_entry.get("score", 0)
                        new_resp["evaluation"] = eval_entry.get("evaluation", "No explanation provided.")
                        evaluated_responses.append(new_resp)
                    else:
                        # Missing entry? fallback to Levenshtein
                        evaluated_responses.extend(self.fallback_strategy.evaluate_answers([resp]))

            except Exception as e:
                print(f"[WARN] Gemini evaluation failed: {e}")
                print(f"[DEBUG] Raw response text: {repr(response_text) if 'response_text' in locals() else 'N/A'}")

                # 🔄 Fallback for all responses
                evaluated_responses = self.fallback_strategy.evaluate_answers(responses)

            return evaluated_responses
   
   
   
    # def evaluate_answer(self, user_answer: str, correct_answer: str) -> Dict[str, Any]:
    #     return super().evaluate_answer(user_answer, correct_answer)

    # def evaluate_answers(self, responses: list) -> list:
    #     """
    #     Evaluate all answers in one batch.
    #     Each item in `responses` is a dict:
    #     {
    #         "question_id": "q1",
    #         "question_text": "...",
    #         "user_answer": "...",
    #         "correct_answer": "...",
    #         "topic_name": "..."
    #     }
    #     Returns the same list with 'score' added to each entry.
    #     """

    #     # Build a single prompt for all answers
    #     batch_prompt = "Compare the following candidate answers to the reference answers:\n\n"
    #     for resp in responses:
    #         batch_prompt += f"Question: {resp['question_text']}\n"
    #         batch_prompt += f"Candidate: {resp['user_answer']}\n"
    #         batch_prompt += f"Reference: {resp['correct_answer']}\n\n"

    #     batch_prompt += (
    #         "For each answer, provide a numeric score (1-5) and a short explanation. "
    #         "Return the results as a JSON list in the following format:\n"
    #         "[{'question_id': 'q1', 'score': 4, 'evaluation': 'short explanation', "
    #         "'topic_name': '...'}, ...]"
    #     )

    #     # Call the Gemini model once
    #     response = self.evaluator.model.generate_content(batch_prompt)

    #     try:
    #         # Extract JSON from markdown code blocks if present
    #         response_text = response.text.strip()
            
    #         if response_text.startswith('```json'):
    #             # Find the JSON content between ```json and ```
    #             start_marker = '```json'
    #             end_marker = '```'
    #             start_idx = response_text.find(start_marker) + len(start_marker)
    #             end_idx = response_text.find(end_marker, start_idx)
                
    #             if end_idx != -1:
    #                 json_content = response_text[start_idx:end_idx].strip()
    #             else:
    #                 # Fallback: remove the opening marker and hope for the best
    #                 json_content = response_text[start_idx:].strip()
    #         elif response_text.startswith('```'):
    #             # Handle generic code blocks
    #             lines = response_text.split('\n')
    #             # Remove first and last lines (the ``` markers)
    #             json_content = '\n'.join(lines[1:-1])
    #         else:
    #             # No code blocks, use as is
    #             json_content = response_text
            
    #         print("Extracted JSON content:", json_content)
            
    #         evaluations_raw = json.loads(json_content)
    #         eval_map = {e["question_id"]: e for e in evaluations_raw}

    #         # Add score to original responses
    #         evaluated_responses = []
    #         for resp in responses:
    #             eval_entry = eval_map.get(resp["question_id"], {})
    #             new_resp = resp.copy()
    #             new_resp["score"] = eval_entry.get("score", 0)
    #             evaluated_responses.append(new_resp)

    #     except Exception as e:
    #         print(f"[WARN] Failed to parse batch evaluation JSON: {e}")
    #         print(f"[DEBUG] Raw response text: {repr(response.text)}")
    #         # Fallback: return responses with score 0
    #         evaluated_responses = []
    #         for resp in responses:
    #             new_resp = resp.copy()
    #             new_resp["score"] = 0
    #             evaluated_responses.append(new_resp)

    #     return evaluated_responses

