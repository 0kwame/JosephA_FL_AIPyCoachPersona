import json
import os
from typing import List, Dict, Any


class QuestionRepository:
    def __init__(self):
        self.__questions: List[Dict[str, Any]] = []
        self.__file_path = os.path.join("db", "questions.json")
        self.__load_questions(self.__file_path)

    def __load_questions(self, file_path: str) -> None:
        try:
            with open(file_path, "r") as file:
                self.__questions = json.load(file)
        except FileNotFoundError:
            print(f"File {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from the file {file_path}.")

    @property
    def questions(self) -> List[Dict[str, Any]]:
        """Return all loaded questions."""
        return self.__questions
