
# FactCheckAgent
# Fact-Check Agent

An AI-powered fact-checking application that extracts factual claims from PDF documents, searches live web evidence, and classifies claims as **Verified**, **Inaccurate**, or **False**.

## Features

* PDF document upload
* Automatic claim extraction
* Live web evidence retrieval
* AI-assisted fact verification
* Confidence scoring
* Source evidence display
* CSV report export
* Modern Streamlit UI

## How It Works

1. Upload a PDF document.
2. The application extracts text from the PDF.
3. Fact-checkable claims are identified automatically.
4. Relevant evidence is retrieved from the web.
5. Claims are analyzed against retrieved evidence.
6. Each claim is classified as:

   * **Verified**
   * **Inaccurate**
   * **False**
7. Results can be exported as a CSV report.

## Technology Stack

### Frontend

* Streamlit

### Backend

* Python

### Libraries

* Pandas
* PyPDF
* Requests
* Python-Dotenv

### AI & Search

* Groq LLM
* Tavily Search API

## Project Structure

```text
fact-check-agent/
│
├── app.py
├── requirements.txt
├── .env
├── README.md
└── assets/
```

## Installation

Clone the repository:

```bash
git clone <your-repository-url>
cd fact-check-agent
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

### macOS/Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file:

```env
TAVILY_API_KEY=your_tavily_api_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

## Run the Application

```bash
streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

## Output

For every extracted claim, the application provides:

* Claim text
* Verification status
* Confidence score
* Reasoning
* Corrected fact (if available)
* Supporting web evidence
* CSV export report

## Future Improvements

* Multi-model verification
* OCR support for scanned PDFs
* Historical fact validation
* Batch document processing
* Source credibility scoring
* Advanced semantic fact matching

## Disclaimer

This project is intended for educational and research purposes. Verification quality depends on the availability and reliability of live web sources.

## Author

Sandeep Yadav
=======
# Fact-Check Agent

A deployed-ready Streamlit web app for automated PDF fact-checking.

## Objective

Marketing PDFs often contain outdated or hallucinated statistics. This app acts as a **Truth Layer**:

1. Upload a PDF
2. Extract fact-checkable claims
3. Search live web data
4. Flag every claim as **Verified**, **Inaccurate**, or **False**
5. Provide corrected facts and source links

## Tech Stack

- Streamlit for UI
- pypdf for PDF text extraction
- OpenAI API for claim extraction and reasoning
- Tavily API for live web search
- Pandas for CSV report export

## Features

- PDF upload UI
- Claim extraction from PDF text
- Live web evidence search
- Automated verification report
- Status labels: Verified, Inaccurate, False
- Correct fact suggestion
- Source links
- CSV report download
- Streamlit Cloud deployment-ready

## Local Setup

```bash
git clone <your-repo-url>
cd fact-check-agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Required Secrets

Create `.streamlit/secrets.toml` locally or add these in Streamlit Cloud secrets:

```toml
OPENAI_API_KEY = "your_openai_api_key"
TAVILY_API_KEY = "your_tavily_api_key"
OPENAI_MODEL = "gpt-4o-mini"
```

## Deployment on Streamlit Cloud

1. Push this project to GitHub.
2. Go to Streamlit Cloud.
3. Click **New app**.
4. Select your GitHub repository.
5. Set main file path as `app.py`.
6. Add secrets:

```toml
OPENAI_API_KEY = "your_openai_api_key"
TAVILY_API_KEY = "your_tavily_api_key"
OPENAI_MODEL = "gpt-4o-mini"
```

7. Deploy and copy your live app URL.

## Submission Format

Submit one document/email containing:

- Deployed App Link: `https://your-app.streamlit.app`
- GitHub Repository: `https://github.com/your-username/fact-check-agent`
- Demo Video: 30-second screen recording

## Notes

- Best results come from text-based PDFs.
- Scanned/image-only PDFs may require OCR, which is not included in this lightweight version.
- If API credits run out, the demo video proves the expected functionality.
>>>>>>> 5f44b49 (initial commit)
