# ✦ Smart Calculator: Desktop & Web (Groq AI Powered)

A modern, high-performance calculator featuring standard calculations, scientific functions, and a nature-language AI assistant powered by **Llama-3.3-70B** via Groq. Designed with a premium dark-mode aesthetic for both Desktop (CustomTkinter) and Web (FastAPI).

![Smart Calculator UI](https://img.shields.io/badge/UI-CustomTkinter-blue) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green) ![AI](https://img.shields.io/badge/AI-Groq%20Llama--3.3-orange)

## ✨ Features

-   **Dual Modes:** Seamlessly switch between a local **Desktop App** and a **Web API**.
-   **🤖 AI Math Assistant:** Ask complex questions in plain English (e.g., "What's an 18% tip on a ₹850 bill?").
-   **📐 Scientific Logic:** Full support for trigonometry, logarithms, and power functions.
-   **📜 Smart History:** Persistent session history with one-click recall of previous results.
-   **⌨ Keyboard Support:** Full Numpad and operator support for lightning-fast calculations.
-   **🎨 Glassmorphism Design:** Modern, eye-catching UI with a premium dark-theme palette.

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have **Python 3.10+** installed.

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/Abhishek-M-34/Calculator.git
cd Calculator
pip install -r requirements.txt
```

### 3. API Setup (Optional for AI)
To use the AI Mode, you need a free Groq API key:
1. Get a key at [console.groq.com](https://console.groq.com/).
2. Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_key_here
   ```

---

## 🛠 How to Run

### 🖥 Desktop Version
The desktop version provides a dedicated window with a sleek interface.
```bash
python calculator.py
```

### 🌐 Web Version
Launch the FastAPI server and open the web interface.
```bash
python -m uvicorn server:app --reload
```
View the app at: **`http://127.0.0.1:8000`**

---

## ☁️ Deployment (Hugging Face)

This project is ready for **Hugging Face Spaces**. 

1.  Create a new **Docker** Space.
2.  Connect your GitHub repository.
3.  Add your `GROQ_API_KEY` to the **Secrets** section in Space Settings.
4.  The `main.py` is pre-configured to handle the Hugging Face port (7860).

---

## 📂 Project Structure

-   `calculator.py`: The Main Desktop application (CustomTkinter).
-   `server.py`: FastAPI backend for the web application.
-   `main.py`: Entry point for Hugging Face deployment.
-   `calculator_core.py`: Shared logic for math evaluation and AI queries.
-   `static/`: Frontend assets (HTML, CSS, JS) for the web version.
-   `.env`: Local environment variables (Git ignored).


