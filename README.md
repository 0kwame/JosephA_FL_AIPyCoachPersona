### 🤖 AI Mock Interviewer BOT

This lab demonstrates an **AI Mock Interviewer BOT** that simulates a technical interview experience. The bot prompts users with questions, evaluates their answers using a fuzzy matching algorithm, and generates a performance report.

The core functionality of the bot includes:

- Using the **command-line interface (CLI)** to interact with users.
- Applying the **Levenshtein distance** algorithm for fuzzy matching.
- Providing a detailed session summary with feedback.

---

### Prerequisites

- **Python** installed on your computer
- A Python package manager such as `uv` or `pip`

---

### How to Use

1.  **Create a virtual environment** (example using `uv`):

    ```bash
    uv venv .venv
    ```

2.  **Activate the virtual environment:**

    ```bash
    source .venv/bin/activate
    ```

3.  **Run the application:**

    ```bash
    uv run main.py
    ```

    The application will start the mock interview session, prompting you with a series of questions and recording your answers.

4.  **Run the tests:**

    ```bash
    uv run -m unittest discover -v
    ```

---

### Tools & Libraries Used

- **Levenshtein**: A library used to implement fuzzy matching by calculating the **Levenshtein distance** between user answers and correct answers.
- **json**: Python's built-in library for handling the question bank stored in a **JSON file**.
- **datetime**: For adding timestamps to session reports.
- **os**: For managing file paths and creating the reports directory.
- **unittest**: Used to implement and run automated tests.

---

### What I Learned

- How to build an interactive command-line application that guides a user through a process.
- How to use the Levenshtein distance algorithm to perform **fuzzy matching**, allowing for flexible and robust answer evaluation.
- The importance of separating concerns by using different services (e.g., an `EvaluationService` for scoring and a `ReportService` for data persistence).
- How to structure and parse data from a **JSON file** to serve as a dynamic question bank.
- The process of generating a structured summary report that provides detailed feedback and improvement tips to users.
- How to use the Strategy Pattern to create more flexible and maintainable software architecture
