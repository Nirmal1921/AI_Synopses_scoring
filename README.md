# Synopsis Scorer

A privacy-conscious Gen AI-powered online application that evaluates the quality of a user-submitted synopsis based on an uploaded article.

## Features

- Score a synopsis against an original article out of 100
- Provide qualitative feedback on the synopsis
- Detailed score breakdown across multiple dimensions
- Strong privacy protection with data anonymization
- No external API calls - all processing done locally
- Supports both PDF and TXT file formats

## Privacy Protection Strategy

This application is designed with privacy as a core principle:

1. **Local Processing**: Uses open-source models from Hugging Face that run locally without sending data to external APIs.
2. **Data Anonymization**: Automatically detects and replaces personally identifiable information:
   - Names and proper nouns are replaced with [NAME]
   - Dates are replaced with [DATE]
   - Email addresses are replaced with [EMAIL]
   - Phone numbers are replaced with [PHONE]
   - URLs are replaced with [URL]
3. **Secure File Handling**: Files are processed in isolated temporary storage
4. **No Data Retention**: All uploaded files and processed text are deleted after scoring is complete

## Scoring Methodology

The application evaluates synopses based on four key dimensions:

1. **Content Coverage (50%)**: How well the synopsis captures the important information from the article
   - Uses sentence embeddings to compare chunks of the article with the synopsis
   - Calculates the percentage of article chunks that are well-represented in the synopsis

2. **Coherence (25%)**: How well the synopsis aligns with the article's focus and structure
   - Measured using the average semantic similarity between article and synopsis

3. **Clarity (15%)**: How readable and well-structured the synopsis is
   - Considers average sentence length and structure
   - Penalizes overly complex or excessively long sentences

4. **Length Ratio (10%)**: Whether the synopsis is an appropriate length relative to the article
   - Ideal ratio is approximately 20% of the article length
   - Penalizes synopses that are either too brief or too detailed

The final score is a weighted average of these four dimensions, providing a comprehensive assessment of synopsis quality.

## Technical Implementation

- **Frontend**: Streamlit for the web interface
- **Language Model**: sentence-transformers/all-MiniLM-L6-v2 from Hugging Face for text embeddings
- **Text Processing**: NLTK for sentence tokenization and text analysis
- **Document Handling**: PyPDF2 for PDF parsing
- **Security**: Custom decorators for secure file processing and cleanup

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/synopsis-scorer.git
cd synopsis-scorer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

### Running the Application

To start the application:

```bash
streamlit run main.py
```

The application will be available at http://localhost:8501 by default.

### Optional: Password Protection

To enable password protection:

1. Create a file named `.streamlit/secrets.toml` with the content:
```toml
password = "Nirmal123"
```

2. Restart the application

## Usage

1. Upload an original article (TXT or PDF format)
2. Upload a synopsis of the article (TXT format)
3. View the evaluation results:
   - Overall score out of 100
   - Detailed score breakdown
   - Qualitative feedback

## License

This project is licensed under the MIT License - see the LICENSE file for details.
