import json
import csv
import os
from datetime import datetime

class ReportService:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_timestamp(self) -> str:
        """Returns a formatted timestamp string."""
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def find_weak_topics(self, results: list) -> list:
        """Identifies topics with the lowest average scores."""
        topic_scores = {}
        for res in results:
            topic_name = res.get("topic_name", "Unknown Topic")
            score = res.get("score", 0)
            if topic_name not in topic_scores:
                topic_scores[topic_name] = {"total_score": 0, "count": 0}
            topic_scores[topic_name]["total_score"] += score
            topic_scores[topic_name]["count"] += 1

        weak_topics = []
        for topic, data in topic_scores.items():
            avg_score = data["total_score"] / data["count"] if data["count"] > 0 else 0
            # A low score is defined as being below a certain threshold, e.g., 3.0
            if avg_score < 3.0:
                weak_topics.append({"topic": topic, "average_score": round(avg_score, 2)})
        
        # Sort by average score to highlight the weakest
        weak_topics.sort(key=lambda x: x["average_score"])
        return weak_topics

    def generate_report(self, session_summary: dict, file_format: str = "json") -> str:
        """
        Generates and saves a session report in the specified format.
        Returns the path to the saved file.
        """
        timestamp = self._get_timestamp()
        filename = f"report_{timestamp}.{file_format}"
        file_path = os.path.join(self.output_dir, filename)

        # Enhance the summary with weak topics
        weak_topics = self.find_weak_topics(session_summary["detailed_results"])
        session_summary["summary"]["improvement_tips"] = [
            f"Focus on '{t['topic']}' (average score: {t['average_score']}). Review these core concepts." 
            for t in weak_topics
        ]

        if file_format.lower() == "json":
            with open(file_path, "w") as f:
                json.dump(session_summary, f, indent=4)
        elif file_format.lower() == "csv":
            self._write_csv(file_path, session_summary)
        else:
            raise ValueError("Unsupported file format. Choose 'json' or 'csv'.")
        
        print(f"✅ Report saved to {file_path}")
        return file_path

    def _write_csv(self, file_path: str, session_summary: dict):
        """Helper method to write data to a CSV file."""
        with open(file_path, "w", newline='') as f:
            writer = csv.writer(f)
            # Write a summary section at the top
            writer.writerow(["--- Session Summary ---"])
            writer.writerow(["Timestamp", self._get_timestamp()])
            for key, value in session_summary["summary"].items():
                if isinstance(value, list):
                    writer.writerow([key] + value)
                else:
                    writer.writerow([key, value])

            writer.writerow([])  # Empty row for spacing
            writer.writerow(["--- Detailed Results ---"])
            
            # Prepare the header for the detailed results
            headers = ["Question", "Your Answer", "Correct Answer", "Score"]
            writer.writerow(headers)
            
            # Write each question's details
            for res in session_summary["detailed_results"]:
                writer.writerow([
                    res.get("question_text", "N/A"),
                    res.get("user_answer", "N/A"),
                    res.get("correct_answer", "N/A"),
                    res.get("score", "N/A")
                ])