import json
import os
from typing import List, Dict, Any


class QuestionRepository:
    def __init__(self):
        # We'll store the entire dataset dictionary here.
        # It contains the "topics" key.
        self.__dataset: Dict[str, Any] = {}
        self.__file_path = os.path.join("db", "questions.json")
        self.__load_questions(self.__file_path)

    def __load_questions(self, file_path: str) -> None:
        try:
            with open(file_path, "r") as file:
                # Load the entire dictionary from the file
                self.__dataset = json.load(file)
        except FileNotFoundError:
            print(f"File {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from the file {file_path}.")

    @property
    def questions(self) -> List[Dict[str, Any]]:
        """Return the list of topics from the loaded dataset."""
        # Use .get() to safely access the "topics" key
        return self.__dataset.get("topics", [])