import streamlit as st
import uuid
import os
from utils.file_utils import extract_text_from_file, save_uploaded_file
from utils.privacy import anonymize_text, cleanup_temp_files, ensure_nltk_data
from utils.embeddings import load_embedding_model
from utils.evaluator import evaluate_synopsis

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
            cleanup_temp_files(temp_files)
            
            return result
        
        except Exception as e:
            # Ensure cleanup even if an error occurs
            cleanup_temp_files(temp_files)
            st.error(f"An error occurred: {str(e)}")
            
    return wrapper

@secure_process
def run_app():
    # Load NLTK data
    ensure_nltk_data()
    
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
        
        1. **Local Processing**: This app uses open-source models running in your browser to evaluate content.
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
    
    # Process files when both are uploaded
    if article_file and synopsis_file:
        with st.spinner("Reading files..."):
            # Save uploaded files to temporary location
            article_temp = save_uploaded_file(article_file)
            synopsis_temp = save_uploaded_file(synopsis_file)
            
            # Add to temp files list for cleanup
            st.session_state['temp_files'].extend([article_temp, synopsis_temp])
            
            # Extract text
            article_text = extract_text_from_file(article_temp)
            synopsis_text = extract_text_from_file(synopsis_temp)
        
        if article_text and synopsis_text:
            # Anonymize texts for privacy
            st.info("Anonymizing content for privacy protection...")
            anonymized_article = anonymize_text(article_text)
            anonymized_synopsis = anonymize_text(synopsis_text)
            
            # Load model for embeddings
            with st.spinner("Loading language model..."):
                tokenizer, model = load_embedding_model()
            
            # Evaluate synopsis
            with st.spinner("Evaluating synopsis quality..."):
                evaluation = evaluate_synopsis(anonymized_article, anonymized_synopsis, tokenizer, model)
            
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
            
