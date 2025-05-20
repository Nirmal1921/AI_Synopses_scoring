import streamlit as st
import os
import tempfile
import uuid
import re
from io import StringIO
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Set page configuration
st.set_page_config(
    page_title="Synopsis Scorer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple access control (optional bonus)
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets.get("password", "synopsis-scorer-demo"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct
        return True

# Privacy functions
def anonymize_text(text):
    """
    Replace names, dates, and specific identifiers with placeholders.
    """
    # Replace dates (simple pattern)
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATE]', text)
    text = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '[DATE]', text)
    
    # Replace emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Replace phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    
    # Replace URLs
    text = re.sub(r'https?://\S+', '[URL]', text)
    
    # Replace proper nouns (crude approximation)
    lines = text.split('\n')
    anonymized_lines = []
    
    for line in lines:
        words = line.split()
        if len(words) > 0:
            # Keep the first word as is (could be capitalized as start of sentence)
            new_words = [words[0]]
            
            # Process remaining words
            for word in words[1:]:
                # If word starts with capital letter and isn't a common word that might be capitalized
                if (word and word[0].isupper() and 
                    word.lower() not in ['i', 'monday', 'tuesday', 'wednesday', 'thursday', 
                                         'friday', 'saturday', 'sunday', 'january', 'february', 
                                         'march', 'april', 'may', 'june', 'july', 'august', 
                                         'september', 'october', 'november', 'december']):
                    new_words.append('[NAME]')
                else:
                    new_words.append(word)
            
            anonymized_lines.append(" ".join(new_words))
        else:
            anonymized_lines.append(line)
    
    return "\n".join(anonymized_lines)

# Function to securely process and clean up data
def secure_process(func):
    def wrapper(*args, **kwargs):
        # Generate a session ID to track this processing
        session_id = str(uuid.uuid4())
        temp_files = []
        
        try:
            # Store session info
            st.session_state['current_session'] = session_id
            st.session_state['temp_files'] = temp_files
            
            # Execute the wrapped function
            result = func(*args, **kwargs)
            
            # Clean up temporary files
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return result
        
        except Exception as e:
            # Ensure cleanup even if an error occurs
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            st.error(f"An error occurred: {str(e)}")
            
    return wrapper

# Function to read files
def read_file(uploaded_file):
    """Extract text from uploaded file (TXT or PDF)"""
    if uploaded_file is None:
        return None
    
    # Create a temporary file to save the uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = tmp.name
        
    # Add to temp files list for cleanup
    if 'temp_files' in st.session_state:
        st.session_state['temp_files'].append(temp_path)
    
    # Extract text based on file type
    if uploaded_file.name.lower().endswith('.pdf'):
        try:
            # Use a simpler method for reading PDFs since PyPDF2 might cause issues
            import pdfplumber
            with pdfplumber.open(temp_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except ImportError:
            # Fallback to reading as text if pdfplumber isn't available
            st.warning("PDF processing library not available. Please upload a text file instead.")
            return None
    else:  # Assume it's a text file
        with open(temp_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

# Function to compute text similarity using TF-IDF and cosine similarity
def compute_similarity(text1, text2):
    """Compute cosine similarity between two texts using TF-IDF"""
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

# Function to split text into chunks
def split_into_chunks(text, num_chunks=10):
    """Split a text into roughly equal chunks"""
    sentences = text.split('. ')
    chunk_size = max(1, len(sentences) // num_chunks)
    chunks = []
    
    for i in range(0, len(sentences), chunk_size):
        chunk = '. '.join(sentences[i:i+chunk_size])
        if not chunk.endswith('.'):
            chunk += '.'
        chunks.append(chunk)
    
    return chunks

# Function to compute chunk-wise similarity
def compute_chunk_similarities(article_text, synopsis_text, num_chunks=10):
    """
    Split the article into chunks and compute similarity with the synopsis
    to better handle longer texts
    """
    # Split article into chunks
    article_chunks = split_into_chunks(article_text, num_chunks)
    
    # Compute similarity for each chunk
    chunk_similarities = []
    for chunk in article_chunks:
        similarity = compute_similarity(chunk, synopsis_text)
        chunk_similarities.append(similarity)
    
    # Return both individual and average similarities
    return chunk_similarities, sum(chunk_similarities) / len(chunk_similarities)

# Function to evaluate synopsis quality
def evaluate_synopsis(article_text, synopsis_text):
    """Evaluate the quality of a synopsis based on the original article"""
    # Compute similarity metrics
    chunk_similarities, avg_similarity = compute_chunk_similarities(article_text, synopsis_text)
    
    # Calculate coverage score (how many chunks are well-represented)
    coverage_threshold = 0.3  # Similarity threshold for "good coverage"
    coverage_percentage = sum(1 for sim in chunk_similarities if sim > coverage_threshold) / len(chunk_similarities)
    
    # Calculate length ratio score (penalize if too short or too long)
    article_word_count = len(article_text.split())
    synopsis_word_count = len(synopsis_text.split())
    ideal_ratio = 0.2  # Synopsis should be ~20% of article length
    actual_ratio = synopsis_word_count / max(1, article_word_count)
    length_ratio_score = 1.0 - min(1.0, abs(actual_ratio - ideal_ratio) / ideal_ratio)
    
    # Calculate coherence score (based on average similarity)
    coherence_score = avg_similarity
    
    # Calculate clarity score (based on sentence structure, simplified here)
    synopsis_sentences = synopsis_text.split('. ')
    avg_sentence_length = sum(len(sent.split()) for sent in synopsis_sentences) / max(1, len(synopsis_sentences))
    clarity_penalty = 0 if 10 <= avg_sentence_length <= 25 else (min(avg_sentence_length, 40) - 25) / 15
    clarity_score = 1.0 - min(1.0, clarity_penalty)
    
    # Calculate final weighted score
    weights = {
        'content_coverage': 0.50,
        'coherence': 0.25,
        'clarity': 0.15,
        'length_ratio': 0.10
    }
    
    scores = {
        'content_coverage': coverage_percentage * 100,
        'coherence': coherence_score * 100,
        'clarity': clarity_score * 100,
        'length_ratio': length_ratio_score * 100
    }
    
    final_score = sum(scores[metric] * weight for metric, weight in weights.items())
    final_score = max(0, min(100, final_score))  # Ensure within 0-100 range
    
    # Generate qualitative feedback
    feedback = []
    
    if scores['content_coverage'] < 60:
        feedback.append("The synopsis misses key information from the article. Consider including more essential points.")
    elif scores['content_coverage'] > 85:
        feedback.append("Excellent coverage of the article's main points.")
        
    if scores['coherence'] < 60:
        feedback.append("The synopsis could be more aligned with the article's focus and structure.")
    elif scores['coherence'] > 85:
        feedback.append("The synopsis captures the essence of the article well.")
        
    if scores['clarity'] < 60:
        feedback.append("Consider simplifying sentence structure for better readability.")
    elif scores['clarity'] > 85:
        feedback.append("The synopsis is clear and well-structured.")
        
    if scores['length_ratio'] < 60:
        if actual_ratio < ideal_ratio:
            feedback.append("The synopsis is too brief relative to the article length.")
        else:
            feedback.append("The synopsis is too detailed for an effective summary.")
    
    # Limit to 2-3 lines of feedback
    if len(feedback) > 3:
        feedback = feedback[:3]
    
    return {
        'final_score': round(final_score, 1),
        'detailed_scores': {k: round(v, 1) for k, v in scores.items()},
        'feedback': feedback
    }

# Function to load sample data for testing
def load_sample_data():
    st.info("Loading sample files for testing...")
    
    sample_article = """Climate change is one of the most pressing issues facing our planet today. Rising global temperatures have led to melting ice caps, rising sea levels, and increasingly severe weather events. The Intergovernmental Panel on Climate Change (IPCC) has reported that human activities, particularly the burning of fossil fuels, are the primary drivers of climate change.

The effects of climate change are far-reaching. Coastal communities face threats from rising seas and stronger storms. Agricultural regions experience shifts in growing seasons and increased drought frequency. Wildlife populations are disrupted as their habitats change faster than they can adapt.

Addressing climate change requires both mitigation and adaptation strategies. Mitigation focuses on reducing greenhouse gas emissions through renewable energy, improved efficiency, and carbon capture technologies. Adaptation involves preparing communities and ecosystems for the changes that are already unavoidable.

International cooperation is essential, with agreements like the Paris Accord setting targets for emissions reductions. However, implementation remains challenging, as countries balance environmental concerns with economic development goals. At the individual level, people can contribute by reducing their carbon footprint through choices in transportation, diet, and consumption.

Despite the challenges, there are reasons for optimism. Renewable energy costs have fallen dramatically, making clean power increasingly competitive with fossil fuels. Many cities and businesses are taking leadership roles in climate action, even when national governments falter. Technological innovations continue to create new possibilities for sustainable development."""
    
    sample_synopsis = """Climate change is a critical global issue caused primarily by human activities like burning fossil fuels. Its effects include melting ice caps, rising sea levels, and extreme weather events that impact coastal communities, agriculture, and wildlife. Addressing the problem requires both mitigation strategies (reducing emissions through renewable energy and improved efficiency) and adaptation planning for unavoidable changes. While international agreements like the Paris Accord set targets, implementation remains difficult as countries balance environmental and economic concerns. Positive developments include falling renewable energy costs, leadership from cities and businesses, and ongoing technological innovations."""
    
    return sample_article, sample_synopsis

# Function to process texts
def process_texts(article_text, synopsis_text):
    # Anonymize texts for privacy
    st.info("Anonymizing content for privacy protection...")
    anonymized_article = anonymize_text(article_text)
    anonymized_synopsis = anonymize_text(synopsis_text)
    
    # Evaluate synopsis
    with st.spinner("Evaluating synopsis quality..."):
        evaluation = evaluate_synopsis(anonymized_article, anonymized_synopsis)
    
    # Display results
    st.subheader("Evaluation Results")
    
    # Display score with a gauge
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
        <div style="text-align:center;">
            <h1 style="font-size:4rem; margin-bottom:0;">{evaluation['final_score']}</h1>
            <p style="font-size:1.5rem; margin-top:0;">out of 100</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display detailed scores (bonus feature)
    with col2:
        st.subheader("Score Breakdown")
        scores = evaluation['detailed_scores']
        
        # Create score bars
        for metric, score in scores.items():
            readable_metric = ' '.join(word.capitalize() for word in metric.split('_'))
            st.markdown(f"**{readable_metric}:** {score}/100")
            st.progress(score / 100)
    
    # Display feedback
    st.subheader("Qualitative Feedback")
    for feedback in evaluation['feedback']:
        st.markdown(f"- {feedback}")
    
    # Add disclaimer
    st.caption("Note: This evaluation is based on algorithmic analysis and may not capture all nuances of quality.")
    
    # Add privacy confirmation
    st.success("✅ Processing complete. All uploaded files and processed text will be deleted.")

# Main app function
@secure_process
def main():
    # Check password if enabled
    if not check_password():
        return
        
    st.title("📝 Synopsis Scorer")
    st.markdown("""
    This application evaluates the quality of a synopsis based on an original article.
    Upload both files to receive a score and feedback.
    """)
    
    # Add privacy notice
    with st.expander("⚠️ Privacy Information"):
        st.markdown("""
        **Privacy Protection Strategy:**
        
        1. **Local Processing**: This app uses open-source libraries to evaluate content locally.
        2. **Data Anonymization**: Names, dates, emails, and other identifiers are replaced with placeholders.
        3. **No Data Storage**: Uploaded files and processed text are deleted after scoring is complete.
        4. **Secure Handling**: All file processing happens in isolated temporary storage.
        
        No data is sent to external APIs or stored permanently.
        """)
    
    # File upload
    col1, col2 = st.columns(2)
    
    with col1:
        article_file = st.file_uploader("Upload Original Article (.txt or .pdf)", type=["txt", "pdf"])
    
    with col2:
        synopsis_file = st.file_uploader("Upload Synopsis (.txt)", type=["txt"])
    
    # Add sample data option
    if st.button("Load Sample Data for Testing"):
        article_text, synopsis_text = load_sample_data()
        process_texts(article_text, synopsis_text)
    
    # Process files when both are uploaded
    elif article_file and synopsis_file:
        with st.spinner("Reading files..."):
            article_text = read_file(article_file)
            synopsis_text = read_file(synopsis_file)
        
        if article_text and synopsis_text:
            process_texts(article_text, synopsis_text)

if __name__ == "__main__":
    main()
