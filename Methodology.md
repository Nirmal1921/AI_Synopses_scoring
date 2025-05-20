# Synopsis Scorer: Scoring Methodology and Privacy Protection

## Scoring Methodology

The Synopsis Scorer application uses a multi-dimensional approach to evaluate the quality of a synopsis. Each dimension captures a different aspect of what makes a good synopsis, and the final score is a weighted combination of these dimensions.

### Scoring Dimensions

1. **Content Coverage (50%)**
   - The most important factor in a synopsis is whether it covers the key information from the original article.
   - Implementation: The application divides the article into approximately 10 chunks and computes semantic similarity between each chunk and the synopsis.
   - It then calculates what percentage of chunks are well-represented in the synopsis (similarity above 0.5).
   - This measures how comprehensively the synopsis covers the important points from the article.

2. **Coherence (25%)**
   - A good synopsis should align with the article's focus and structure.
   - Implementation: Calculated as the average semantic similarity between the article and synopsis.
   - This measures how well the synopsis captures the essence and meaning of the article.

3. **Clarity (15%)**
   - A synopsis should be clear and readable with appropriate sentence structure.
   - Implementation: Analyzes sentence length and structure, with an ideal range of 10-25 words per sentence.
   - Sentences that are too long or too short are penalized.

4. **Length Ratio (10%)**
   - A synopsis should be concise but complete, typically around 20% of the article's length.
   - Implementation: Calculates the ratio of synopsis length to article length and compares to the ideal ratio.
   - Penalizes synopses that are either too brief (missing information) or too detailed (not a proper summary).

The final score is calculated as:
```
Final Score = (Content Coverage × 0.50) + (Coherence × 0.25) + (Clarity × 0.15) + (Length Ratio × 0.10)
```

## Privacy Protection Strategy

The application implements several privacy protection mechanisms to ensure that sensitive information is not exposed:

### 1. Local Processing
- All text analysis is performed using open-source models that run locally in the application.
- No data is sent to external APIs like OpenAI or Anthropic.
- The Hugging Face Transformers library is used to load and run models locally.

### 2. Data Anonymization
The application automatically detects and replaces potentially sensitive information:
- **Names and proper nouns**: Replaced with [NAME]
- **Dates**: Replaced with [DATE]
- **Email addresses**: Replaced with [EMAIL]
- **Phone numbers**: Replaced with [PHONE]
- **URLs**: Replaced with [URL]

The anonymization process:
1. Uses regular expressions to identify structured information like emails, dates, and URLs.
2. Uses sentence tokenization to detect proper nouns (words that begin with capital letters but aren't at the start of sentences and aren't common capitalized words).

### 3. Secure File Handling
- Files are processed in isolated temporary storage.
- Each upload generates a unique session ID to track associated temporary files.
- A secure processing decorator ensures cleanup even if errors occur.

### 4. No Data Retention
- All uploaded files are immediately deleted after processing.
- No database or persistent storage is used.
- Application state is maintained only for the duration of the session.

### 5. Optional Access Control
- Basic password protection can be enabled to restrict access to authorized users.
- Passwords are not stored in the application state after validation.

This comprehensive approach ensures that the Synopsis Scorer can provide valuable feedback while maintaining strict privacy standards and protecting sensitive information.
