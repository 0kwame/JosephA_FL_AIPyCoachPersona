import Levenshtein
from typing import List, Dict, Any


class EvaluationService:
    """
    Encapsulates all logic related to evaluating user answers against
    correct answers, using the Levenshtein package for scoring.
    """

    def __init__(self):
        self.metrics = {}

    def _calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculates the Levenshtein distance between two strings using
        the Levenshtein package.
        """
        # The package handles the calculation efficiently.
        # It's better to convert both strings to lowercase for a case-insensitive comparison.
        return Levenshtein.distance(s1.lower(), s2.lower())

    def calculate_score(self, user_answer: str, correct_answer: str) -> int:
        """
        Calculates a score (0-5) based on the normalized Levenshtein distance.
        A score of 5 means a perfect match.
        """
        distance = self._calculate_levenshtein_distance(user_answer, correct_answer)
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

    def evaluate_answers(self, user_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        total_score = 0
        
        for response in user_responses:
            user_answer = response.get("user_answer", "")
            correct_answer = response.get("correct_answer", "")
            score = self.calculate_score(user_answer, correct_answer)
            total_score += score
            
            # Corrected part: include topic_name in the results dictionary
            results.append({
                "question_id": response.get("question_id"),
                "question_text": response.get("question_text"),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "score": score,
                "topic_name": response.get("topic_name", "Unknown Topic")  # <-- Add this line
            })

        num_questions = len(user_responses)
        average_score = total_score / num_questions if num_questions > 0 else 0

        return {
            "detailed_results": results,
            "summary": {
                "total_score": total_score,
                "max_possible_score": num_questions * 5,
                "average_score_per_question": round(average_score, 2)
            }
        }