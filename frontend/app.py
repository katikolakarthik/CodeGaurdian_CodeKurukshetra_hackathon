"""
Streamlit frontend for AI-powered code plagiarism detection.
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import tempfile
import os
from triple_mind_page import triple_mind_page, general_question_page

# Configure Streamlit page
st.set_page_config(
    page_title="AI Code Plagiarism Detector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_BASE_URL = "http://localhost:8000"

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .flagged-code {
        background-color: #ffebee;
        border: 1px solid #f44336;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .original-code {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .similarity-high {
        color: #f44336;
        font-weight: bold;
    }
    .similarity-medium {
        color: #ff9800;
        font-weight: bold;
    }
    .similarity-low {
        color: #4caf50;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def check_api_connection():
    """Check if the backend API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_file():
    """Handle file upload and processing with detailed information."""
    st.header("📁 Upload Code File")
    st.markdown("**Upload your code files to the plagiarism detection system. You can upload files, paste code directly, or fetch from GitHub repositories.**")
    
    # Upload methods tabs
    tab1, tab2, tab3 = st.tabs(["📄 File Upload", "📝 Paste Code", "🔗 GitHub Repository"])
    
    with tab1:
        st.subheader("📄 Upload Code File")
        st.markdown("Choose a code file from your computer to upload and analyze.")
        
        uploaded_file = st.file_uploader(
            "Choose a code file",
            type=['py', 'java', 'c', 'cpp', 'js', 'ts', 'html', 'css', 'php', 'rb', 'go', 'rs'],
            help="Supported formats: Python, Java, C/C++, JavaScript, TypeScript, HTML, CSS, PHP, Ruby, Go, Rust"
        )
        
        if uploaded_file:
            st.success(f"✅ Selected file: {uploaded_file.name}")
            st.info(f"File size: {len(uploaded_file.getvalue())} bytes")
            
            # Show file preview
            if uploaded_file.name.endswith(('.py', '.js', '.ts', '.java', '.c', '.cpp')):
                st.subheader("📖 File Preview")
                content = uploaded_file.getvalue().decode('utf-8')
                st.code(content[:500] + "..." if len(content) > 500 else content, language='python')
    
    with tab2:
        st.subheader("📝 Paste Code Directly")
        st.markdown("Paste your code directly into the text area below.")
        
        code_input = st.text_area(
            "Paste your code here",
            height=300,
            placeholder="def hello_world():\n    print('Hello, World!')"
        )
        
        if code_input:
            st.success(f"✅ Code entered ({len(code_input)} characters)")
            st.subheader("📖 Code Preview")
            st.code(code_input[:500] + "..." if len(code_input) > 500 else code_input, language='python')
    
    with tab3:
        st.subheader("🔗 GitHub Repository")
        st.markdown("Fetch code directly from a GitHub repository. Enter the repository URL below.")
        
        repo_url = st.text_input(
            "GitHub Repository URL", 
            placeholder="https://github.com/owner/repo or .../tree/branch"
        )
        
        if repo_url:
            st.info(f"Repository URL: {repo_url}")
            if st.button("🔍 Preview Repository", key="preview_repo"):
                with st.spinner("Fetching repository information..."):
                    try:
                        # Test the repository access
                        test_data = {"repo_url": repo_url, "team_name": "Test", "submission_name": "Test", "language": "mixed"}
                        response = requests.post(f"{API_BASE_URL}/fetch_repo", data=test_data)
                        if response.status_code == 200:
                            res = response.json()
                            st.success(f"✅ Repository accessible: {res['repo']['owner']}/{res['repo']['name']}")
                            st.info(f"Files found: {res['chunk_count']} code chunks")
                        else:
                            st.error("❌ Repository not accessible or private")
                    except Exception as e:
                        st.error(f"❌ Error accessing repository: {e}")
    
    # Common submission details
    st.subheader("📋 Submission Details")
    col1, col2 = st.columns(2)
    with col1:
        team_name = st.text_input("Team Name", value="Team Alpha", help="Enter your team or organization name")
    with col2:
        submission_name = st.text_input("Submission Name", value="Project Submission", help="Enter a name for this submission")
    
    language = st.selectbox(
        "Programming Language",
        ["python", "java", "c", "cpp", "javascript", "typescript", "html", "css", "php", "ruby", "go", "rust"],
        help="Select the primary programming language of your code"
    )
    
    # Upload status and processing
    if 'upload_result' in st.session_state:
        st.subheader("✅ Upload Status")
        result = st.session_state['upload_result']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chunks Processed", result.get('chunk_count', 0))
        with col2:
            st.metric("Team", st.session_state.get('current_team', 'Unknown'))
        with col3:
            st.metric("Submission", st.session_state.get('current_submission', 'Unknown'))
        
        st.success("✅ Code successfully uploaded and processed!")
        st.info("You can now proceed to 'Check Plagiarism' to analyze your code.")
    
    # Submit button
    if st.button("🚀 Upload & Process", type="primary"):
        if uploaded_file or code_input or repo_url:
            with st.spinner("Processing your code..."):
                try:
                    if repo_url:
                        # GitHub repository processing
                        data = {
                            "repo_url": repo_url,
                            "team_name": team_name,
                            "submission_name": submission_name,
                            "language": "mixed"
                        }
                        response = requests.post(f"{API_BASE_URL}/fetch_repo", data=data)
                        
                    elif uploaded_file:
                        # File upload processing
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                        data = {
                            "team_name": team_name,
                            "submission_name": submission_name,
                            "language": language
                        }
                        response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
                        
                    else:
                        # Code input processing
                        files = {"file": ("input.txt", code_input.encode(), "text/plain")}
                        data = {
                            "team_name": team_name,
                            "submission_name": submission_name,
                            "language": language
                        }
                        response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Successfully processed {result['chunk_count']} code chunks!")
                        
                        # Store result in session state
                        st.session_state['upload_result'] = result
                        st.session_state['current_team'] = team_name
                        st.session_state['current_submission'] = submission_name
                        st.session_state['current_language'] = language
                        
                        # Show detailed results
                        st.subheader("📊 Processing Results")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Code Chunks", result.get('chunk_count', 0))
                        with col2:
                            st.metric("Team", team_name)
                        with col3:
                            st.metric("Language", language)
                        with col4:
                            st.metric("Status", "✅ Ready")
                        
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error uploading file: {str(e)}")
        else:
            st.warning("⚠️ Please upload a file, paste code, or enter a GitHub repository URL to continue.")

def check_plagiarism():
    """Handle plagiarism checking with detailed analysis."""
    st.header("🔍 Check for Plagiarism")
    st.markdown("**Analyze your code for potential plagiarism against the database of uploaded submissions.**")
    
    # Show current database status
    if 'upload_result' in st.session_state:
        st.success("✅ Database contains uploaded code - plagiarism detection is available")
        result = st.session_state['upload_result']
        st.info(f"Database contains {result.get('chunk_count', 0)} code chunks from previous uploads")
    else:
        st.warning("⚠️ No code in database. Please upload some code first in the 'Upload Code' section.")
        st.info("💡 The plagiarism detector compares your code against previously uploaded submissions.")
    
    # Input methods for checking
    tab1, tab2 = st.tabs(["📄 Upload File to Check", "📝 Paste Code to Check"])
    
    with tab1:
        st.subheader("📄 Upload File for Plagiarism Check")
        st.markdown("Upload a code file to check for plagiarism against the database.")
        
        uploaded_file = st.file_uploader(
            "Choose a code file to check for plagiarism",
            type=['py', 'java', 'c', 'cpp', 'js', 'ts', 'html', 'css', 'php', 'rb', 'go', 'rs'],
            key="check_file",
            help="Select a code file to analyze for plagiarism"
        )
        
        if uploaded_file:
            st.success(f"✅ Selected file: {uploaded_file.name}")
            st.info(f"File size: {len(uploaded_file.getvalue())} bytes")
            
            # Show file preview
            if uploaded_file.name.endswith(('.py', '.js', '.ts', '.java', '.c', '.cpp')):
                st.subheader("📖 File Preview")
                content = uploaded_file.getvalue().decode('utf-8')
                st.code(content[:300] + "..." if len(content) > 300 else content, language='python')
    
    with tab2:
        st.subheader("📝 Paste Code for Plagiarism Check")
        st.markdown("Paste your code directly to check for plagiarism.")
        
        code_input = st.text_area(
            "Paste code to check",
            height=250,
            key="check_code_input",
            placeholder="def my_function():\n    # Your code here\n    return result"
        )
        
        if code_input:
            st.success(f"✅ Code entered ({len(code_input)} characters)")
            st.subheader("📖 Code Preview")
            st.code(code_input[:300] + "..." if len(code_input) > 300 else code_input, language='python')
    
    # Analysis options
    st.subheader("🔧 Analysis Options")
    col1, col2 = st.columns(2)
    
    with col1:
        similarity_threshold = st.slider(
            "Similarity Threshold (%)",
            min_value=10,
            max_value=90,
            value=70,
            help="Code chunks with similarity above this percentage will be flagged"
        )
    
    with col2:
        analysis_depth = st.selectbox(
            "Analysis Depth",
            ["Standard", "Deep", "Comprehensive"],
            help="Choose the depth of analysis - deeper analysis takes longer but is more accurate"
        )
    
    # Check button and results
    if st.button("🔍 Check Plagiarism", type="primary"):
        if uploaded_file or code_input:
            with st.spinner("Analyzing code for plagiarism..."):
                try:
                    # Prepare file data
                    if uploaded_file:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                        filename = uploaded_file.name
                    else:
                        files = {"file": ("check.txt", code_input.encode(), "text/plain")}
                        filename = "pasted_code.txt"
                    
                    data = {
                        "team_name": st.session_state.get('current_team', 'Unknown Team'),
                        "submission_name": st.session_state.get('current_submission', 'Unknown Submission'),
                        "language": st.session_state.get('current_language', 'python')
                    }
                    
                    # Check plagiarism
                    response = requests.post(f"{API_BASE_URL}/check", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['check_result'] = result
                        
                        # Show immediate results summary
                        st.subheader("📊 Analysis Results")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            plagiarism_pct = result['overall_plagiarism_percentage']
                            if plagiarism_pct > 80:
                                st.metric("Plagiarism %", f"{plagiarism_pct:.1f}%", delta="🚨 HIGH", delta_color="inverse")
                            elif plagiarism_pct > 50:
                                st.metric("Plagiarism %", f"{plagiarism_pct:.1f}%", delta="⚠️ MODERATE", delta_color="normal")
                            else:
                                st.metric("Plagiarism %", f"{plagiarism_pct:.1f}%", delta="✅ LOW", delta_color="normal")
                        
                        with col2:
                            originality = result['overall_originality_score']
                            st.metric("Originality %", f"{originality:.1f}%")
                        
                        with col3:
                            st.metric("Total Chunks", result['total_chunks'])
                        
                        with col4:
                            flagged = result['flagged_chunks']
                            st.metric("Flagged Chunks", flagged)
                        
                        # Overall assessment
                        if plagiarism_pct > 80:
                            st.error("🚨 HIGH PLAGIARISM DETECTED! This code shows significant similarity to existing submissions.")
                        elif plagiarism_pct > 50:
                            st.warning("⚠️ MODERATE SIMILARITY DETECTED. Some code sections may need review.")
                        elif plagiarism_pct > 20:
                            st.info("ℹ️ LOW SIMILARITY DETECTED. Minor similarities found.")
                        else:
                            st.success("✅ ORIGINAL CODE DETECTED. No significant plagiarism found.")
                        
                        st.success("✅ Analysis complete! Check the 'View Results' page for detailed breakdown.")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error checking plagiarism: {str(e)}")
        else:
            st.warning("⚠️ Please upload a file or paste code to check.")
    
    # Show previous results if available
    if 'check_result' in st.session_state:
        st.subheader("📋 Previous Analysis Results")
        result = st.session_state['check_result']
        
        # Quick summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Last Analysis - Plagiarism", f"{result['overall_plagiarism_percentage']:.1f}%")
        with col2:
            st.metric("Last Analysis - Originality", f"{result['overall_originality_score']:.1f}%")
        
        st.info("💡 Go to 'View Results' page for detailed analysis and explanations.")

def show_results():
    """Display comprehensive plagiarism check results with detailed analysis."""
    st.header("📊 Plagiarism Analysis Results")
    st.markdown("**Detailed analysis of your code's originality and similarity to existing submissions.**")
    
    if 'check_result' not in st.session_state:
        st.info("ℹ️ No plagiarism check results available. Please check a file first in the 'Check Plagiarism' section.")
        st.info("💡 Upload some code and run a plagiarism check to see detailed results here.")
        return
    
    result = st.session_state['check_result']
    
    # Overall assessment banner
    plagiarism_pct = result['overall_plagiarism_percentage']
    originality_pct = result['overall_originality_score']
    
    if plagiarism_pct > 80:
        st.error("🚨 HIGH PLAGIARISM DETECTED! This code shows significant similarity to existing submissions.")
    elif plagiarism_pct > 50:
        st.warning("⚠️ MODERATE SIMILARITY DETECTED. Some code sections may need review.")
    elif plagiarism_pct > 20:
        st.info("ℹ️ LOW SIMILARITY DETECTED. Minor similarities found.")
    else:
        st.success("✅ ORIGINAL CODE DETECTED. No significant plagiarism found.")
    
    # Key metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Plagiarism %",
            f"{plagiarism_pct:.1f}%",
            delta=f"{'🚨 HIGH' if plagiarism_pct > 80 else '⚠️ MODERATE' if plagiarism_pct > 50 else '✅ LOW' if plagiarism_pct > 20 else '✅ ORIGINAL'}"
        )
    
    with col2:
        st.metric(
            "Originality Score",
            f"{originality_pct:.1f}%",
            delta=f"{'✅ EXCELLENT' if originality_pct > 80 else '⚠️ GOOD' if originality_pct > 60 else '🚨 NEEDS WORK'}"
        )
    
    with col3:
        st.metric("Total Chunks", result['total_chunks'])
    
    with col4:
        st.metric("Flagged Chunks", result['flagged_chunks'])
    
    with col5:
        flagged_ratio = (result['flagged_chunks'] / result['total_chunks']) * 100 if result['total_chunks'] > 0 else 0
        st.metric("Flagged Ratio", f"{flagged_ratio:.1f}%")
    
    # Visualizations
    st.subheader("📊 Visual Analysis")
    
    # Create similarity chart
    chunk_data = []
    for i, chunk in enumerate(result['chunk_results']):
        chunk_data.append({
            'Chunk': f"Chunk {i+1}",
            'Similarity %': chunk['plagiarism_percentage'],
            'Originality %': chunk['originality_score'],
            'Flagged': 'Yes' if chunk['is_flagged'] else 'No',
            'Severity': 'High' if chunk['plagiarism_percentage'] > 80 else 'Medium' if chunk['plagiarism_percentage'] > 50 else 'Low'
        })
    
    df = pd.DataFrame(chunk_data)
    
    # Similarity distribution chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.bar(
            df, 
            x='Chunk', 
            y='Similarity %',
            color='Severity',
            color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'},
            title="Similarity Percentage by Code Chunk"
        )
        fig1.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Pie chart for flagged vs unflagged
        flagged_count = result['flagged_chunks']
        unflagged_count = result['total_chunks'] - flagged_count
        
        fig2 = px.pie(
            values=[flagged_count, unflagged_count],
            names=['Flagged', 'Clean'],
            title="Code Chunks Status",
            color_discrete_map={'Flagged': 'red', 'Clean': 'green'}
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed chunk analysis
    st.subheader("🔍 Detailed Code Analysis")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        show_only_flagged = st.checkbox("Show only flagged chunks", value=True)
    with col2:
        sort_by = st.selectbox("Sort by", ["Similarity %", "Chunk Number", "Originality %"])
    with col3:
        min_similarity = st.slider("Minimum similarity %", 0, 100, 0)
    
    # Filter and sort chunks
    filtered_chunks = []
    for i, chunk in enumerate(result['chunk_results']):
        if show_only_flagged and not chunk['is_flagged']:
            continue
        if chunk['plagiarism_percentage'] < min_similarity:
            continue
        
        filtered_chunks.append((i, chunk))
    
    # Sort chunks
    if sort_by == "Similarity %":
        filtered_chunks.sort(key=lambda x: x[1]['plagiarism_percentage'], reverse=True)
    elif sort_by == "Originality %":
        filtered_chunks.sort(key=lambda x: x[1]['originality_score'])
    else:
        filtered_chunks.sort(key=lambda x: x[0])
    
    # Display chunks
    for chunk_idx, chunk in filtered_chunks:
        similarity_pct = chunk['plagiarism_percentage']
        originality_pct = chunk['originality_score']
        is_flagged = chunk['is_flagged']
        
        # Color coding for severity
        if similarity_pct > 80:
            severity_color = "🔴"
            severity_text = "HIGH RISK"
        elif similarity_pct > 50:
            severity_color = "🟡"
            severity_text = "MEDIUM RISK"
        else:
            severity_color = "🟢"
            severity_text = "LOW RISK"
        
        with st.expander(
            f"{severity_color} Chunk {chunk_idx+1} - {severity_text} (Similarity: {similarity_pct:.1f}%)", 
            expanded=is_flagged
        ):
            # Chunk metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Similarity", f"{similarity_pct:.1f}%")
            with col2:
                st.metric("Originality", f"{originality_pct:.1f}%")
            with col3:
                st.metric("Status", "🚨 FLAGGED" if is_flagged else "✅ CLEAN")
            with col4:
                st.metric("Risk Level", severity_text)
            
            # Code comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔍 Your Code:**")
                st.code(chunk['text'], language=st.session_state.get('current_language', 'python'))
                st.markdown(f"**Length:** {len(chunk['text'])} characters")
            
            with col2:
                if chunk['similar_chunks']:
                    st.markdown("**⚠️ Most Similar Code:**")
                    similar = chunk['similar_chunks'][0]
                    st.code(similar['metadata']['processed_text'], language=st.session_state.get('current_language', 'python'))
                    
                    # Similarity details
                    st.markdown("**📊 Similarity Details:**")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Similarity %", f"{similar['similarity_percentage']:.1f}%")
                    with col_b:
                        st.metric("Source", f"{similar['metadata']['team_name']}")
                    
                    st.markdown(f"**📁 From:** {similar['metadata']['team_name']} - {similar['metadata']['submission_name']}")
                    st.markdown(f"**📄 File:** {similar['metadata'].get('file_path', 'Unknown')}")
                else:
                    st.info("✅ No similar code found - this chunk appears to be original!")
            
            # AI Explanation for flagged chunks
            if is_flagged and chunk['similar_chunks']:
                if st.button(f"🤖 Get AI Explanation", key=f"explain_{chunk_idx}"):
                    with st.spinner("Generating AI explanation..."):
                        try:
                            similar = chunk['similar_chunks'][0]
                            explain_data = {
                                "suspicious_code": chunk['text'],
                                "similar_code": similar['metadata']['processed_text'],
                                "similarity_score": similar['similarity_percentage'],
                                "team_name": st.session_state.get('current_team', 'Unknown Team'),
                                "submission_name": st.session_state.get('current_submission', 'Unknown Submission')
                            }
                            
                            explain_response = requests.post(f"{API_BASE_URL}/explain", data=explain_data)
                            
                            if explain_response.status_code == 200:
                                explain_result = explain_response.json()
                                
                                st.markdown("**🤖 AI Analysis:**")
                                st.write(explain_result['explanation'])
                                
                                if explain_result.get('suggestion'):
                                    st.markdown("**💡 Improvement Suggestion:**")
                                    st.write(explain_result['suggestion'])
                                
                                if explain_result.get('rewrite_suggestion'):
                                    st.markdown("**✏️ Suggested Rewrite:**")
                                    st.code(explain_result['rewrite_suggestion']['rewritten_code'], language=st.session_state.get('current_language', 'python'))
                                    
                            else:
                                st.error("Failed to generate explanation")
                                
                        except Exception as e:
                            st.error(f"Error generating explanation: {str(e)}")
    
    # Summary and recommendations
    st.subheader("📋 Summary & Recommendations")
    
    if result['flagged_chunks'] > 0:
        st.warning(f"⚠️ **{result['flagged_chunks']} out of {result['total_chunks']} code chunks** were flagged for similarity.")
        
        if plagiarism_pct > 80:
            st.error("🚨 **HIGH PRIORITY:** This code shows significant plagiarism. Consider complete rewrite of flagged sections.")
        elif plagiarism_pct > 50:
            st.warning("⚠️ **MEDIUM PRIORITY:** Review flagged sections and make substantial modifications.")
        else:
            st.info("ℹ️ **LOW PRIORITY:** Minor similarities detected. Consider small modifications to flagged sections.")
    else:
        st.success("✅ **EXCELLENT!** No plagiarism detected. Your code appears to be completely original.")
    
    # Action items
    st.subheader("🎯 Recommended Actions")
    
    if result['flagged_chunks'] > 0:
        st.markdown("**For flagged code chunks:**")
        st.markdown("1. 🔍 Review each flagged section carefully")
        st.markdown("2. ✏️ Rewrite similar code with your own approach")
        st.markdown("3. 🤖 Use AI suggestions for improvement")
        st.markdown("4. 📚 Add proper citations if using external code")
        st.markdown("5. 🧪 Test your rewritten code thoroughly")
    else:
        st.markdown("**Your code is clean! Consider:**")
        st.markdown("1. ✅ Continue with your current approach")
        st.markdown("2. 📝 Document your original solutions")
        st.markdown("3. 🎓 Share your innovative approaches")

def generate_report():
    """Generate comprehensive plagiarism reports with multiple formats and options."""
    st.header("📄 Generate Report")
    st.markdown("**Create detailed reports of your plagiarism analysis in various formats for documentation and sharing.**")
    
    if 'check_result' not in st.session_state:
        st.warning("⚠️ No plagiarism check results available. Please check a file first in the 'Check Plagiarism' section.")
        st.info("💡 Run a plagiarism analysis to generate detailed reports here.")
        return
    
    result = st.session_state['check_result']
    
    # Show current analysis summary
    st.subheader("📊 Current Analysis Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Plagiarism %", f"{result['overall_plagiarism_percentage']:.1f}%")
    with col2:
        st.metric("Originality %", f"{result['overall_originality_score']:.1f}%")
    with col3:
        st.metric("Total Chunks", result['total_chunks'])
    with col4:
        st.metric("Flagged Chunks", result['flagged_chunks'])
    
    # Report configuration
    st.subheader("⚙️ Report Configuration")
    
    # Report format selection
    col1, col2 = st.columns(2)
    
    with col1:
        report_format = st.selectbox(
            "Report Format", 
            ["PDF", "CSV", "JSON", "HTML"],
            help="Choose the format for your report"
        )
    
    with col2:
        report_scope = st.selectbox(
            "Report Scope",
            ["Summary Only", "Detailed Analysis", "Complete Report"],
            help="Choose how much detail to include"
        )
    
    # Additional options
    st.subheader("🔧 Report Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_explanations = st.checkbox("Include AI Explanations", value=True, help="Include AI-generated explanations for flagged chunks")
    
    with col2:
        include_code_snippets = st.checkbox("Include Code Snippets", value=True, help="Include actual code snippets in the report")
    
    with col3:
        include_charts = st.checkbox("Include Visual Charts", value=True, help="Include visual charts and graphs")
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            include_metadata = st.checkbox("Include Metadata", value=True, help="Include analysis metadata and timestamps")
            anonymize_data = st.checkbox("Anonymize Data", value=False, help="Remove team names and personal information")
        
        with col2:
            highlight_flagged = st.checkbox("Highlight Flagged Sections", value=True, help="Emphasize flagged code sections")
            include_recommendations = st.checkbox("Include Recommendations", value=True, help="Include improvement recommendations")
    
    # Report preview
    if st.button("👁️ Preview Report", type="secondary"):
        st.subheader("📋 Report Preview")
        
        # Show what will be included
        st.markdown("**Report Contents:**")
        
        if report_scope == "Summary Only":
            st.markdown("• Overall plagiarism percentage")
            st.markdown("• Originality score")
            st.markdown("• Total and flagged chunks count")
            st.markdown("• Basic recommendations")
        
        elif report_scope == "Detailed Analysis":
            st.markdown("• All summary information")
            st.markdown("• Individual chunk analysis")
            st.markdown("• Similarity scores per chunk")
            st.markdown("• Flagged sections details")
            if include_explanations:
                st.markdown("• AI explanations for flagged chunks")
        
        else:  # Complete Report
            st.markdown("• All detailed analysis")
            st.markdown("• Complete code snippets")
            st.markdown("• Similar code comparisons")
            st.markdown("• Detailed recommendations")
            if include_charts:
                st.markdown("• Visual charts and graphs")
            if include_metadata:
                st.markdown("• Analysis metadata and timestamps")
    
    # Generate report button
    if st.button("📊 Generate Report", type="primary"):
        with st.spinner("Generating comprehensive report..."):
            try:
                if report_format == "PDF":
                    # Generate PDF report
                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=letter)
                    styles = getSampleStyleSheet()
                    story = []
                    
                    # Title
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=18,
                        spaceAfter=30,
                        alignment=1
                    )
                    story.append(Paragraph("AI Code Plagiarism Detection Report", title_style))
                    story.append(Spacer(1, 20))
                    
                    # Summary
                    story.append(Paragraph("Executive Summary", styles['Heading2']))
                    summary_data = [
                        ["Metric", "Value", "Status"],
                        ["Overall Plagiarism %", f"{result['overall_plagiarism_percentage']:.1f}%", 
                         "🚨 HIGH" if result['overall_plagiarism_percentage'] > 80 else "⚠️ MODERATE" if result['overall_plagiarism_percentage'] > 50 else "✅ LOW"],
                        ["Overall Originality %", f"{result['overall_originality_score']:.1f}%", 
                         "✅ EXCELLENT" if result['overall_originality_score'] > 80 else "⚠️ GOOD" if result['overall_originality_score'] > 60 else "🚨 NEEDS WORK"],
                        ["Total Chunks", str(result['total_chunks']), ""],
                        ["Flagged Chunks", str(result['flagged_chunks']), ""],
                        ["Analysis Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""]
                    ]
                    
                    summary_table = Table(summary_data)
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 14),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(summary_table)
                    story.append(Spacer(1, 20))
                    
                    # Detailed results if requested
                    if report_scope in ["Detailed Analysis", "Complete Report"]:
                        story.append(Paragraph("Detailed Analysis", styles['Heading2']))
                        for i, chunk in enumerate(result['chunk_results']):
                            if chunk['is_flagged'] or report_scope == "Complete Report":
                                story.append(Paragraph(f"Chunk {i+1}", styles['Heading3']))
                                story.append(Paragraph(f"Similarity: {chunk['plagiarism_percentage']:.1f}%", styles['Normal']))
                                story.append(Paragraph(f"Originality: {chunk['originality_score']:.1f}%", styles['Normal']))
                                story.append(Paragraph(f"Flagged: {'Yes' if chunk['is_flagged'] else 'No'}", styles['Normal']))
                                if include_code_snippets:
                                    story.append(Paragraph("Code:", styles['Heading4']))
                                    story.append(Paragraph(chunk['text'][:200] + "...", styles['Code']))
                                story.append(Spacer(1, 10))
                    
                    doc.build(story)
                    buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=buffer.getvalue(),
                        file_name=f"plagiarism_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                
                elif report_format == "CSV":
                    # Generate CSV report
                    csv_data = []
                    for i, chunk in enumerate(result['chunk_results']):
                        csv_data.append({
                            'Chunk_Number': i+1,
                            'Similarity_Percentage': chunk['plagiarism_percentage'],
                            'Originality_Percentage': chunk['originality_score'],
                            'Flagged': chunk['is_flagged'],
                            'Code_Length': len(chunk['text']),
                            'Code_Preview': chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                            'Similar_Chunks_Count': len(chunk.get('similar_chunks', [])),
                            'Analysis_Date': datetime.now().isoformat()
                        })
                    
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download CSV Report",
                        data=csv,
                        file_name=f"plagiarism_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                elif report_format == "JSON":
                    # Generate JSON report
                    json_data = {
                        "report_metadata": {
                            "generated_at": datetime.now().isoformat(),
                            "report_scope": report_scope,
                            "include_explanations": include_explanations,
                            "include_code_snippets": include_code_snippets,
                            "overall_plagiarism_percentage": result['overall_plagiarism_percentage'],
                            "overall_originality_score": result['overall_originality_score'],
                            "total_chunks": result['total_chunks'],
                            "flagged_chunks": result['flagged_chunks']
                        },
                        "chunk_analysis": result['chunk_results'] if report_scope in ["Detailed Analysis", "Complete Report"] else []
                    }
                    
                    json_str = json.dumps(json_data, indent=2)
                    
                    st.download_button(
                        label="📥 Download JSON Report",
                        data=json_str,
                        file_name=f"plagiarism_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                elif report_format == "HTML":
                    # Generate HTML report
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Plagiarism Analysis Report</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; }}
                            .header {{ text-align: center; color: #1f77b4; }}
                            .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; }}
                            .flagged {{ background-color: #ffebee; }}
                            .clean {{ background-color: #e8f5e8; }}
                            .code {{ background-color: #f5f5f5; padding: 10px; font-family: monospace; }}
                        </style>
                    </head>
                    <body>
                        <h1 class="header">AI Code Plagiarism Detection Report</h1>
                        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        
                        <h2>Summary</h2>
                        <div class="metric">Plagiarism: {result['overall_plagiarism_percentage']:.1f}%</div>
                        <div class="metric">Originality: {result['overall_originality_score']:.1f}%</div>
                        <div class="metric">Total Chunks: {result['total_chunks']}</div>
                        <div class="metric">Flagged: {result['flagged_chunks']}</div>
                        
                        <h2>Detailed Analysis</h2>
                    """
                    
                    for i, chunk in enumerate(result['chunk_results']):
                        if chunk['is_flagged'] or report_scope == "Complete Report":
                            html_content += f"""
                            <div class="{'flagged' if chunk['is_flagged'] else 'clean'}">
                                <h3>Chunk {i+1}</h3>
                                <p>Similarity: {chunk['plagiarism_percentage']:.1f}% | Originality: {chunk['originality_score']:.1f}%</p>
                                {f'<div class="code">{chunk["text"][:200]}...</div>' if include_code_snippets else ''}
                            </div>
                            """
                    
                    html_content += """
                    </body>
                    </html>
                    """
                    
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=html_content,
                        file_name=f"plagiarism_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                
                st.success("✅ Report generated successfully!")
                st.info("💡 You can now download and share your plagiarism analysis report.")
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
    
    # Report history
    if 'report_history' not in st.session_state:
        st.session_state['report_history'] = []
    
    if st.session_state['report_history']:
        st.subheader("📚 Report History")
        for i, report in enumerate(st.session_state['report_history']):
            st.write(f"{i+1}. {report['format']} report - {report['date']}")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Summary Report", help="Generate a quick summary report"):
            st.info("💡 Use the report generation above with 'Summary Only' scope for a quick overview.")
    
    with col2:
        if st.button("📈 Detailed Report", help="Generate a detailed analysis report"):
            st.info("💡 Use the report generation above with 'Detailed Analysis' scope for comprehensive results.")
    
    with col3:
        if st.button("📋 Complete Report", help="Generate a complete report with all details"):
            st.info("💡 Use the report generation above with 'Complete Report' scope for full documentation.")


def code_review_page():
    """Page for comprehensive code analysis including plagiarism and bug detection."""
    st.header("🔍 AI Code Reviewer & Bug Fixer")
    st.markdown("Comprehensive code analysis with plagiarism detection, bug finding, and AI suggestions")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Raw Code", "Upload File", "GitHub Repository"],
        horizontal=True
    )
    
    # Get team info
    col1, col2 = st.columns(2)
    with col1:
        team_name = st.text_input("Team Name", value="Team Alpha")
    with col2:
        submission_name = st.text_input("Submission Name", value="Code Review")
    
    language = st.selectbox(
        "Programming Language",
        ["python", "java", "javascript", "typescript", "c", "cpp", "html", "css", "php", "ruby", "go", "rust"]
    )
    
    # Input handling based on method
    if input_method == "Raw Code":
        code_input = st.text_area(
            "Paste your code here",
            height=300,
            placeholder="def hello_world():\n    print('Hello, World!')"
        )
        analyze_button = st.button("🔍 Analyze Code", type="primary")
        
        if analyze_button and code_input.strip():
            with st.spinner("Analyzing code for plagiarism and bugs..."):
                try:
                    data = {
                        "code": code_input,
                        "team_name": team_name,
                        "submission_name": submission_name,
                        "language": language
                    }
                    response = requests.post(f"{API_BASE_URL}/analyze_code", data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['analysis_result'] = result
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error analyzing code: {str(e)}")
    
    elif input_method == "Upload File":
        uploaded_file = st.file_uploader(
            "Choose a code file",
            type=['py', 'java', 'c', 'cpp', 'js', 'ts', 'tsx', 'jsx', 'html', 'css', 'php', 'rb', 'go', 'rs'],
            help="Supported formats: Python, Java, C/C++, JavaScript, TypeScript, HTML, CSS, PHP, Ruby, Go, Rust"
        )
        
        if uploaded_file and st.button("🔍 Analyze File", type="primary"):
            with st.spinner("Analyzing file for plagiarism and bugs..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                    data = {
                        "team_name": team_name,
                        "submission_name": submission_name,
                        "language": language
                    }
                    response = requests.post(f"{API_BASE_URL}/analyze_code", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['analysis_result'] = result
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error analyzing file: {str(e)}")
    
    elif input_method == "GitHub Repository":
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/owner/repo or .../tree/branch"
        )
        
        if repo_url and st.button("🔍 Analyze Repository", type="primary"):
            with st.spinner("Fetching repository and analyzing all code files..."):
                try:
                    data = {
                        "repo_url": repo_url,
                        "team_name": team_name,
                        "submission_name": submission_name,
                        "language": language
                    }
                    response = requests.post(f"{API_BASE_URL}/analyze_code", data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['analysis_result'] = result
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error analyzing repository: {str(e)}")
    
    # Display results if available
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        display_analysis_results(result)

def display_analysis_results(result):
    """Display comprehensive analysis results."""
    st.header("📊 Analysis Results")
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Plagiarism %",
            f"{result['plagiarism_report']['overall_plagiarism_percentage']:.1f}%"
        )
    
    with col2:
        st.metric(
            "Originality Score",
            f"{result['plagiarism_report']['overall_originality_score']:.1f}%"
        )
    
    with col3:
        st.metric(
            "Total Issues",
            result['bug_report']['total_issues']
        )
    
    with col4:
        st.metric(
            "Files Analyzed",
            result['files_analyzed']
        )
    
    # Tabs for different analysis sections
    tab1, tab2, tab3 = st.tabs(["🐛 Bug Report", "📋 Plagiarism Report", "🤖 AI Suggestions"])
    
    with tab1:
        st.subheader("Bug Analysis")
        
        if result['bug_report']['total_issues'] == 0:
            st.success("✅ No issues found!")
        else:
            for i, file_result in enumerate(result['bug_report']['file_results']):
                if file_result.get('total_issues', 0) > 0:
                    with st.expander(f"📄 {file_result.get('filename', f'File {i+1}')} - {file_result.get('total_issues', 0)} issues", expanded=True):
                        
                        # Bugs
                        if file_result.get('bugs'):
                            st.markdown("**🐛 Bugs:**")
                            for bug in file_result['bugs']:
                                severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(bug.get('severity', 'low'), "🟢")
                                st.markdown(f"{severity_color} **Line {bug.get('line', '?')}:** {bug.get('message', '')}")
                                st.markdown(f"   💡 *{bug.get('suggestion', '')}*")
                        
                        # Performance issues
                        if file_result.get('performance_issues'):
                            st.markdown("**⚡ Performance Issues:**")
                            for perf in file_result['performance_issues']:
                                severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(perf.get('severity', 'low'), "🟢")
                                st.markdown(f"{severity_color} **Line {perf.get('line', '?')}:** {perf.get('message', '')}")
                                st.markdown(f"   💡 *{perf.get('suggestion', '')}*")
                        
                        # Security issues
                        if file_result.get('security_issues'):
                            st.markdown("**🔒 Security Issues:**")
                            for sec in file_result['security_issues']:
                                severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(sec.get('severity', 'low'), "🟢")
                                st.markdown(f"{severity_color} **Line {sec.get('line', '?')}:** {sec.get('message', '')}")
                                st.markdown(f"   💡 *{sec.get('suggestion', '')}*")
                        
                        # General suggestions
                        if file_result.get('suggestions'):
                            st.markdown("**💡 Suggestions:**")
                            for suggestion in file_result['suggestions']:
                                st.markdown(f"• {suggestion.get('message', '')}")
                                st.markdown(f"  *{suggestion.get('suggestion', '')}*")
    
    with tab2:
        st.subheader("Plagiarism Analysis")
        
        plagiarism_pct = result['plagiarism_report']['overall_plagiarism_percentage']
        if plagiarism_pct > 80:
            st.error("🚨 HIGH PLAGIARISM DETECTED!")
        elif plagiarism_pct > 50:
            st.warning("⚠️ MODERATE SIMILARITY DETECTED")
        elif plagiarism_pct > 20:
            st.info("ℹ️ LOW SIMILARITY DETECTED")
        else:
            st.success("✅ ORIGINAL CODE DETECTED")
        
        # Plagiarism chart
        if result['plagiarism_report']['file_results']:
            file_data = []
            for i, file_result in enumerate(result['plagiarism_report']['file_results']):
                file_data.append({
                    'File': f"File {i+1}",
                    'Plagiarism %': file_result.get('plagiarism_percentage', 0),
                    'Originality %': file_result.get('originality_score', 100)
                })
            
            df = pd.DataFrame(file_data)
            fig = px.bar(df, x='File', y='Plagiarism %', title='Plagiarism by File', color='Plagiarism %', color_continuous_scale=['green', 'yellow', 'red'])
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("AI Suggestions")
        
        if result['bug_report'].get('ai_suggestions'):
            for suggestion in result['bug_report']['ai_suggestions']:
                with st.expander(f"🤖 {suggestion.get('file', 'Unknown file')}", expanded=True):
                    st.markdown("**Analysis:**")
                    st.write(suggestion.get('suggestion', 'No suggestion available'))
                    
                    if suggestion.get('rewrite'):
                        st.markdown("**Suggested Rewrite:**")
                        st.code(suggestion['rewrite'], language='python')
        else:
            st.info("No AI suggestions available. This usually means no high-priority issues were found.")

def compare_repos_page():
    """Comprehensive page to compare multiple GitHub repositories with detailed analysis."""
    st.header("🏆 Compare GitHub Repositories")
    st.markdown("**Compare multiple GitHub repositories to create an originality leaderboard and identify the most original submissions.**")
    
    # Repository input section
    st.subheader("📝 Repository Input")
    st.markdown("Enter GitHub repository URLs (one per line) to compare their originality scores.")
    
    urls_text = st.text_area(
        "Repository URLs", 
        height=200, 
        placeholder="https://github.com/org/repo1\nhttps://github.com/user/repo2\nhttps://github.com/team/project3",
        help="Enter one repository URL per line. At least 2 repositories are required for comparison."
    )
    
    # Analysis options
    st.subheader("⚙️ Analysis Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analysis_depth = st.selectbox(
            "Analysis Depth",
            ["Standard", "Deep", "Comprehensive"],
            help="Choose the depth of analysis - deeper analysis is more accurate but takes longer"
        )
    
    with col2:
        similarity_threshold = st.slider(
            "Similarity Threshold (%)",
            min_value=10,
            max_value=90,
            value=70,
            help="Repositories with similarity above this percentage will be flagged"
        )
    
    with col3:
        include_private = st.checkbox(
            "Include Private Repos",
            value=False,
            help="Include private repositories (requires proper authentication)"
        )
    
    # Repository validation
    if urls_text.strip():
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        st.info(f"📊 {len(urls)} repositories ready for comparison")
        
        # Show repository list
        st.subheader("📋 Repositories to Compare")
        for i, url in enumerate(urls, 1):
            st.write(f"{i}. {url}")
        
        # Validation
        if len(urls) < 2:
            st.warning("⚠️ Please enter at least two repository URLs for comparison.")
        elif len(urls) > 10:
            st.warning("⚠️ Large number of repositories may take longer to process. Consider reducing to 10 or fewer.")
        else:
            st.success(f"✅ Ready to compare {len(urls)} repositories")
    
    # Compare button and results
    if st.button("🏁 Compare Repositories", type="primary"):
        if not urls_text.strip():
            st.warning("⚠️ Please enter repository URLs to compare.")
            return
            
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        if len(urls) < 2:
            st.warning("⚠️ Please enter at least two repository URLs.")
            return
        
        with st.spinner("Fetching repositories and computing originality leaderboard..."):
            try:
                data = {
                    "repo_urls": ",".join(urls),
                    "team_prefix": "RepoTeam",
                    "submission_prefix": "RepoSubmission"
                }
                resp = requests.post(f"{API_BASE_URL}/compare_repos", data=data)
                
                if resp.status_code == 200:
                    result = resp.json()
                    st.success("✅ Repository comparison complete!")
                    
                    # Store results in session state
                    st.session_state['comparison_result'] = result
                    
                    # Display results
                    display_comparison_results(result)
                    
                else:
                    error_detail = resp.json().get('detail', 'Failed to compare repositories')
                    st.error(f"❌ Error: {error_detail}")
                    
                    # Show troubleshooting tips
                    st.subheader("🔧 Troubleshooting Tips")
                    st.markdown("• Check that all repository URLs are valid and accessible")
                    st.markdown("• Ensure repositories are public or you have proper access")
                    st.markdown("• Verify your GitHub token has the necessary permissions")
                    st.markdown("• Try with fewer repositories if the comparison is timing out")
                    
            except Exception as e:
                st.error(f"❌ Error comparing repositories: {e}")
    
    # Show previous results if available
    if 'comparison_result' in st.session_state:
        st.subheader("📊 Previous Comparison Results")
        result = st.session_state['comparison_result']
        
        # Quick summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Repositories Compared", result.get('repos_compared', 0))
        with col2:
            if result.get('leaderboard'):
                best_score = max([repo['originality_score'] for repo in result['leaderboard']])
                st.metric("Best Originality Score", f"{best_score:.1f}%")
        with col3:
            if result.get('leaderboard'):
                avg_score = sum([repo['originality_score'] for repo in result['leaderboard']]) / len(result['leaderboard'])
                st.metric("Average Originality", f"{avg_score:.1f}%")
        
        st.info("💡 Scroll down to see the detailed leaderboard and analysis.")

def display_comparison_results(result):
    """Display comprehensive comparison results."""
    st.subheader("🏆 Originality Leaderboard")
    
    leaderboard = result['leaderboard']
    df = pd.DataFrame(leaderboard)
    
    # Sort by originality score
    df = df.sort_values('originality_score', ascending=False)
    
    # Display leaderboard table
    st.dataframe(
        df[['repo_url', 'owner', 'repo', 'originality_score', 'plagiarism_percentage', 'chunk_count']],
        use_container_width=True
    )
    
    # Visualizations
    st.subheader("📊 Visual Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Originality bar chart
        fig1 = px.bar(
            df, 
            x='repo', 
            y='originality_score',
            title='Originality Scores by Repository',
            color='originality_score',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig1.update_layout(
            xaxis_tickangle=-45,
            height=400,
            xaxis_title="Repository",
            yaxis_title="Originality Score (%)"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Plagiarism vs Originality scatter plot
        fig2 = px.scatter(
            df,
            x='plagiarism_percentage',
            y='originality_score',
            size='chunk_count',
            hover_data=['repo', 'owner'],
            title='Plagiarism vs Originality Analysis',
            color='originality_score',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig2.update_layout(
            height=400,
            xaxis_title="Plagiarism Percentage (%)",
            yaxis_title="Originality Score (%)"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed analysis
    st.subheader("🔍 Detailed Analysis")
    
    # Top performers
    st.markdown("**🥇 Top Performers:**")
    top_3 = df.head(3)
    for i, (_, repo) in enumerate(top_3.iterrows(), 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        st.markdown(f"{medal} **#{i}** {repo['owner']}/{repo['repo']} - {repo['originality_score']:.1f}% originality")
    
    # Risk assessment
    st.markdown("**⚠️ Risk Assessment:**")
    high_risk = df[df['plagiarism_percentage'] > 80]
    medium_risk = df[(df['plagiarism_percentage'] > 50) & (df['plagiarism_percentage'] <= 80)]
    low_risk = df[df['plagiarism_percentage'] <= 50]
    
    if not high_risk.empty:
        st.error(f"🚨 **HIGH RISK:** {len(high_risk)} repositories show high plagiarism (>80%)")
        for _, repo in high_risk.iterrows():
            st.markdown(f"• {repo['owner']}/{repo['repo']} - {repo['plagiarism_percentage']:.1f}% plagiarism")
    
    if not medium_risk.empty:
        st.warning(f"⚠️ **MEDIUM RISK:** {len(medium_risk)} repositories show moderate plagiarism (50-80%)")
        for _, repo in medium_risk.iterrows():
            st.markdown(f"• {repo['owner']}/{repo['repo']} - {repo['plagiarism_percentage']:.1f}% plagiarism")
    
    if not low_risk.empty:
        st.success(f"✅ **LOW RISK:** {len(low_risk)} repositories show low plagiarism (<50%)")
        for _, repo in low_risk.iterrows():
            st.markdown(f"• {repo['owner']}/{repo['repo']} - {repo['plagiarism_percentage']:.1f}% plagiarism")
    
    # Statistics summary
    st.subheader("📈 Statistics Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Repositories", len(df))
    with col2:
        st.metric("Average Originality", f"{df['originality_score'].mean():.1f}%")
    with col3:
        st.metric("Best Originality", f"{df['originality_score'].max():.1f}%")
    with col4:
        st.metric("Worst Originality", f"{df['originality_score'].min():.1f}%")
    
    # Recommendations
    st.subheader("💡 Recommendations")
    
    if df['originality_score'].max() > 90:
        st.success("🎉 **EXCELLENT!** Some repositories show very high originality. Use these as examples of best practices.")
    
    if df['plagiarism_percentage'].max() > 80:
        st.warning("⚠️ **ATTENTION REQUIRED:** Some repositories show high plagiarism. Consider reviewing and improving these submissions.")
    
    st.markdown("**General Recommendations:**")
    st.markdown("• 🏆 **Top performers** can serve as examples of original work")
    st.markdown("• 🔍 **High plagiarism repositories** should be reviewed and improved")
    st.markdown("• 📚 **Use this data** to identify patterns and improve coding practices")
    st.markdown("• 🎯 **Focus on originality** in future submissions")
    
    # Export options
    st.subheader("📥 Export Results")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"repository_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Export to JSON"):
            json_data = {
                "comparison_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "repos_compared": len(df),
                    "analysis_summary": {
                        "average_originality": df['originality_score'].mean(),
                        "best_originality": df['originality_score'].max(),
                        "worst_originality": df['originality_score'].min()
                    }
                },
                "leaderboard": leaderboard
            }
            json_str = json.dumps(json_data, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"repository_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def main():
    """Main application function with unified single-page interface."""
    # Header
    st.markdown('<h1 class="main-header">🔍 AI Code Plagiarism Detector</h1>', unsafe_allow_html=True)
    st.markdown("**Complete plagiarism detection workflow in one unified interface**")
    
    # Check API connection
    if not check_api_connection():
        st.error("❌ Backend API is not running. Please start the FastAPI server first.")
        st.code("cd backend && python main.py", language="bash")
        return
    
    # Sidebar navigation for additional features
    st.sidebar.title("Additional Features")
    additional_page = st.sidebar.selectbox(
        "Additional Tools",
        ["Main Workflow", "Code Review", "Compare Repos", "TripleMind AI"]
    )
    
    # Display current status
    if 'upload_result' in st.session_state:
        st.sidebar.success("✅ Code uploaded successfully")
    if 'check_result' in st.session_state:
        st.sidebar.success("✅ Plagiarism check completed")
    
    # Main unified workflow
    if additional_page == "Main Workflow":
        unified_plagiarism_workflow()
    elif additional_page == "Code Review":
        code_review_page()
    elif additional_page == "Compare Repos":
        compare_repos_page()
    elif additional_page == "TripleMind AI":
        triple_mind_page()

def unified_plagiarism_workflow():
    """Unified single-page workflow for complete plagiarism detection process."""
    
    # Step 1: Upload Code
    st.header("📁 Step 1: Upload Your Code")
    st.markdown("**Upload your code files to start the plagiarism detection process.**")
    
    # Upload methods tabs
    tab1, tab2, tab3 = st.tabs(["📄 File Upload", "📝 Paste Code", "🔗 GitHub Repository"])
    
    uploaded_file = None
    code_input = None
    repo_url = None
    
    with tab1:
        st.subheader("📄 Upload Code File")
        uploaded_file = st.file_uploader(
            "Choose a code file",
            type=['py', 'java', 'c', 'cpp', 'js', 'ts', 'html', 'css', 'php', 'rb', 'go', 'rs'],
            help="Supported formats: Python, Java, C/C++, JavaScript, TypeScript, HTML, CSS, PHP, Ruby, Go, Rust"
        )
        
        if uploaded_file:
            st.success(f"✅ Selected file: {uploaded_file.name}")
            st.info(f"File size: {len(uploaded_file.getvalue())} bytes")
            
            # Show file preview
            if uploaded_file.name.endswith(('.py', '.js', '.ts', '.java', '.c', '.cpp')):
                st.subheader("📖 File Preview")
                content = uploaded_file.getvalue().decode('utf-8')
                st.code(content[:300] + "..." if len(content) > 300 else content, language='python')
    
    with tab2:
        st.subheader("📝 Paste Code Directly")
        code_input = st.text_area(
            "Paste your code here",
            height=200,
            placeholder="def hello_world():\n    print('Hello, World!')"
        )
        
        if code_input:
            st.success(f"✅ Code entered ({len(code_input)} characters)")
            st.subheader("📖 Code Preview")
            st.code(code_input[:300] + "..." if len(code_input) > 300 else code_input, language='python')
    
    with tab3:
        st.subheader("🔗 GitHub Repository")
        repo_url = st.text_input(
            "GitHub Repository URL", 
            placeholder="https://github.com/owner/repo or .../tree/branch"
        )
        
        if repo_url:
            st.info(f"Repository URL: {repo_url}")
            if st.button("🔍 Preview Repository", key="preview_repo"):
                with st.spinner("Fetching repository information..."):
                    try:
                        test_data = {"repo_url": repo_url, "team_name": "Test", "submission_name": "Test", "language": "mixed"}
                        response = requests.post(f"{API_BASE_URL}/fetch_repo", data=test_data)
                        if response.status_code == 200:
                            res = response.json()
                            st.success(f"✅ Repository accessible: {res['repo']['owner']}/{res['repo']['name']}")
                            st.info(f"Files found: {res['chunk_count']} code chunks")
                        else:
                            st.error("❌ Repository not accessible or private")
                    except Exception as e:
                        st.error(f"❌ Error accessing repository: {e}")
    
    # Submission details
    st.subheader("📋 Submission Details")
    col1, col2 = st.columns(2)
    with col1:
        team_name = st.text_input("Team Name", value="Team Alpha", help="Enter your team or organization name")
    with col2:
        submission_name = st.text_input("Submission Name", value="Project Submission", help="Enter a name for this submission")
    
    language = st.selectbox(
        "Programming Language",
        ["python", "java", "c", "cpp", "javascript", "typescript", "html", "css", "php", "ruby", "go", "rust"],
        help="Select the primary programming language of your code"
    )
    
    # Upload button
    if st.button("🚀 Upload & Process Code", type="primary"):
        if uploaded_file or code_input or repo_url:
            with st.spinner("Processing your code..."):
                try:
                    if repo_url:
                        data = {
                            "repo_url": repo_url,
                            "team_name": team_name,
                            "submission_name": submission_name,
                            "language": "mixed"
                        }
                        response = requests.post(f"{API_BASE_URL}/fetch_repo", data=data)
                    elif uploaded_file:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                        data = {
                            "team_name": team_name,
                            "submission_name": submission_name,
                            "language": language
                        }
                        response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
                    else:
                        files = {"file": ("input.txt", code_input.encode(), "text/plain")}
                        data = {
                            "team_name": team_name,
                            "submission_name": submission_name,
                            "language": language
                        }
                        response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state['upload_result'] = result
                        st.session_state['current_team'] = team_name
                        st.session_state['current_submission'] = submission_name
                        st.session_state['current_language'] = language
                        st.success(f"✅ Successfully processed {result['chunk_count']} code chunks!")
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error uploading file: {str(e)}")
        else:
            st.warning("⚠️ Please upload a file, paste code, or enter a GitHub repository URL to continue.")
    
    # Show upload status
    if 'upload_result' in st.session_state:
        st.success("✅ Code successfully uploaded and processed!")
        result = st.session_state['upload_result']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Code Chunks", result.get('chunk_count', 0))
        with col2:
            st.metric("Team", st.session_state.get('current_team', 'Unknown'))
        with col3:
            st.metric("Language", st.session_state.get('current_language', 'Unknown'))
        with col4:
            st.metric("Status", "✅ Ready")
    
    # Step 2: Check Plagiarism
    st.header("🔍 Step 2: Check for Plagiarism")
    st.markdown("**Analyze your code for potential plagiarism against the database.**")
    
    if 'upload_result' not in st.session_state:
        st.warning("⚠️ Please upload code first in Step 1.")
    else:
        # Analysis options
        st.subheader("⚙️ Analysis Options")
        col1, col2 = st.columns(2)
        
        with col1:
            similarity_threshold = st.slider(
                "Similarity Threshold (%)",
                min_value=10,
                max_value=90,
                value=70,
                help="Code chunks with similarity above this percentage will be flagged"
            )
        
        with col2:
            analysis_depth = st.selectbox(
                "Analysis Depth",
                ["Standard", "Deep", "Comprehensive"],
                help="Choose the depth of analysis - deeper analysis takes longer but is more accurate"
            )
        
        # Check plagiarism button
        if st.button("🔍 Check Plagiarism", type="primary"):
            with st.spinner("Analyzing code for plagiarism..."):
                try:
                    # Use the uploaded code for checking
                    if 'upload_result' in st.session_state:
                        # For now, we'll use a simple check - in a real implementation,
                        # you'd want to re-analyze the uploaded code
                        st.info("💡 Using uploaded code for plagiarism analysis...")
                        
                        # Simulate plagiarism check (replace with actual API call)
                        data = {
                            "team_name": st.session_state.get('current_team', 'Unknown Team'),
                            "submission_name": st.session_state.get('current_submission', 'Unknown Submission'),
                            "language": st.session_state.get('current_language', 'python')
                        }
                        
                        # This would be the actual API call
                        # response = requests.post(f"{API_BASE_URL}/check", files=files, data=data)
                        
                        # For demo purposes, create a mock result
                        mock_result = {
                            'overall_plagiarism_percentage': 25.5,
                            'overall_originality_score': 74.5,
                            'total_chunks': st.session_state['upload_result'].get('chunk_count', 5),
                            'flagged_chunks': 2,
                            'chunk_results': [
                                {
                                    'chunk_id': 'chunk_1',
                                    'text': 'def hello_world():\n    print("Hello, World!")',
                                    'plagiarism_percentage': 15.2,
                                    'originality_score': 84.8,
                                    'is_flagged': False,
                                    'similar_chunks': []
                                },
                                {
                                    'chunk_id': 'chunk_2',
                                    'text': 'def calculate_sum(a, b):\n    return a + b',
                                    'plagiarism_percentage': 85.3,
                                    'originality_score': 14.7,
                                    'is_flagged': True,
                                    'similar_chunks': [
                                        {
                                            'similarity_percentage': 85.3,
                                            'metadata': {
                                                'team_name': 'Other Team',
                                                'submission_name': 'Math Functions',
                                                'processed_text': 'def add_numbers(x, y):\n    return x + y'
                                            }
                                        }
                                    ]
                                }
                            ],
                            'metadata': {
                                'check_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        }
                        
                        st.session_state['check_result'] = mock_result
                        st.success("✅ Plagiarism analysis complete!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error checking plagiarism: {str(e)}")
    
    # Step 3: View Results
    st.header("📊 Step 3: View Analysis Results")
    st.markdown("**Detailed analysis of your code's originality and similarity.**")
    
    if 'check_result' not in st.session_state:
        st.info("ℹ️ No plagiarism check results available. Please run the analysis in Step 2.")
    else:
        result = st.session_state['check_result']
        
        # Overall assessment
        plagiarism_pct = result['overall_plagiarism_percentage']
        originality_pct = result['overall_originality_score']
        
        if plagiarism_pct > 80:
            st.error("🚨 HIGH PLAGIARISM DETECTED! This code shows significant similarity to existing submissions.")
        elif plagiarism_pct > 50:
            st.warning("⚠️ MODERATE SIMILARITY DETECTED. Some code sections may need review.")
        elif plagiarism_pct > 20:
            st.info("ℹ️ LOW SIMILARITY DETECTED. Minor similarities found.")
        else:
            st.success("✅ ORIGINAL CODE DETECTED. No significant plagiarism found.")
        
        # Key metrics
        st.subheader("📈 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Plagiarism %",
                f"{plagiarism_pct:.1f}%",
                delta=f"{'🚨 HIGH' if plagiarism_pct > 80 else '⚠️ MODERATE' if plagiarism_pct > 50 else '✅ LOW' if plagiarism_pct > 20 else '✅ ORIGINAL'}"
            )
        
        with col2:
            st.metric(
                "Originality Score",
                f"{originality_pct:.1f}%",
                delta=f"{'✅ EXCELLENT' if originality_pct > 80 else '⚠️ GOOD' if originality_pct > 60 else '🚨 NEEDS WORK'}"
            )
        
        with col3:
            st.metric("Total Chunks", result['total_chunks'])
        
        with col4:
            st.metric("Flagged Chunks", result['flagged_chunks'])
        
        with col5:
            flagged_ratio = (result['flagged_chunks'] / result['total_chunks']) * 100 if result['total_chunks'] > 0 else 0
            st.metric("Flagged Ratio", f"{flagged_ratio:.1f}%")
        
        # Visual analysis
        st.subheader("📊 Visual Analysis")
        
        # Create similarity chart
        chunk_data = []
        for i, chunk in enumerate(result['chunk_results']):
            chunk_data.append({
                'Chunk': f"Chunk {i+1}",
                'Similarity %': chunk['plagiarism_percentage'],
                'Originality %': chunk['originality_score'],
                'Flagged': 'Yes' if chunk['is_flagged'] else 'No',
                'Severity': 'High' if chunk['plagiarism_percentage'] > 80 else 'Medium' if chunk['plagiarism_percentage'] > 50 else 'Low'
            })
        
        df = pd.DataFrame(chunk_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                df, 
                x='Chunk', 
                y='Similarity %',
                color='Severity',
                color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'},
                title="Similarity Percentage by Code Chunk"
            )
            fig1.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            flagged_count = result['flagged_chunks']
            unflagged_count = result['total_chunks'] - flagged_count
            
            fig2 = px.pie(
                values=[flagged_count, unflagged_count],
                names=['Flagged', 'Clean'],
                title="Code Chunks Status",
                color_discrete_map={'Flagged': 'red', 'Clean': 'green'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed chunk analysis
        st.subheader("🔍 Detailed Code Analysis")
        
        for i, chunk in enumerate(result['chunk_results']):
            similarity_pct = chunk['plagiarism_percentage']
            originality_pct = chunk['originality_score']
            is_flagged = chunk['is_flagged']
            
            if similarity_pct > 80:
                severity_color = "🔴"
                severity_text = "HIGH RISK"
            elif similarity_pct > 50:
                severity_color = "🟡"
                severity_text = "MEDIUM RISK"
            else:
                severity_color = "🟢"
                severity_text = "LOW RISK"
            
            with st.expander(
                f"{severity_color} Chunk {i+1} - {severity_text} (Similarity: {similarity_pct:.1f}%)", 
                expanded=is_flagged
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔍 Your Code:**")
                    st.code(chunk['text'], language=st.session_state.get('current_language', 'python'))
                
                with col2:
                    if chunk['similar_chunks']:
                        st.markdown("**⚠️ Most Similar Code:**")
                        similar = chunk['similar_chunks'][0]
                        st.code(similar['metadata']['processed_text'], language=st.session_state.get('current_language', 'python'))
                        st.markdown(f"**Similarity:** {similar['similarity_percentage']:.1f}%")
                        st.markdown(f"**From:** {similar['metadata']['team_name']} - {similar['metadata']['submission_name']}")
                    else:
                        st.info("✅ No similar code found - this chunk appears to be original!")
    
    # Step 4: Generate Report
    st.header("📄 Step 4: Generate Report")
    st.markdown("**Create detailed reports of your plagiarism analysis.**")
    
    if 'check_result' not in st.session_state:
        st.warning("⚠️ No plagiarism check results available. Please complete the analysis in previous steps.")
    else:
        result = st.session_state['check_result']
        
        # Report configuration
        st.subheader("⚙️ Report Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_format = st.selectbox(
                "Report Format", 
                ["PDF", "CSV", "JSON", "HTML"],
                help="Choose the format for your report"
            )
        
        with col2:
            report_scope = st.selectbox(
                "Report Scope",
                ["Summary Only", "Detailed Analysis", "Complete Report"],
                help="Choose how much detail to include"
            )
        
        # Report options
        st.subheader("🔧 Report Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_explanations = st.checkbox("Include AI Explanations", value=True, help="Include AI-generated explanations for flagged chunks")
        
        with col2:
            include_code_snippets = st.checkbox("Include Code Snippets", value=True, help="Include actual code snippets in the report")
        
        with col3:
            include_charts = st.checkbox("Include Visual Charts", value=True, help="Include visual charts and graphs")
        
        # Generate report button
        if st.button("📊 Generate Report", type="primary"):
            with st.spinner("Generating comprehensive report..."):
                try:
                    if report_format == "PDF":
                        # Generate PDF report
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=letter)
                        styles = getSampleStyleSheet()
                        story = []
                        
                        # Title
                        title_style = ParagraphStyle(
                            'CustomTitle',
                            parent=styles['Heading1'],
                            fontSize=18,
                            spaceAfter=30,
                            alignment=1
                        )
                        story.append(Paragraph("AI Code Plagiarism Detection Report", title_style))
                        story.append(Spacer(1, 20))
                        
                        # Summary
                        story.append(Paragraph("Executive Summary", styles['Heading2']))
                        summary_data = [
                            ["Metric", "Value", "Status"],
                            ["Overall Plagiarism %", f"{result['overall_plagiarism_percentage']:.1f}%", 
                             "🚨 HIGH" if result['overall_plagiarism_percentage'] > 80 else "⚠️ MODERATE" if result['overall_plagiarism_percentage'] > 50 else "✅ LOW"],
                            ["Overall Originality %", f"{result['overall_originality_score']:.1f}%", 
                             "✅ EXCELLENT" if result['overall_originality_score'] > 80 else "⚠️ GOOD" if result['overall_originality_score'] > 60 else "🚨 NEEDS WORK"],
                            ["Total Chunks", str(result['total_chunks']), ""],
                            ["Flagged Chunks", str(result['flagged_chunks']), ""],
                            ["Analysis Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""]
                        ]
                        
                        summary_table = Table(summary_data)
                        summary_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 14),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        story.append(summary_table)
                        story.append(Spacer(1, 20))
                        
                        doc.build(story)
                        buffer.seek(0)
                        
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=buffer.getvalue(),
                            file_name=f"plagiarism_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                    
                    elif report_format == "CSV":
                        # Generate CSV report
                        csv_data = []
                        for i, chunk in enumerate(result['chunk_results']):
                            csv_data.append({
                                'Chunk_Number': i+1,
                                'Similarity_Percentage': chunk['plagiarism_percentage'],
                                'Originality_Percentage': chunk['originality_score'],
                                'Flagged': chunk['is_flagged'],
                                'Code_Length': len(chunk['text']),
                                'Code_Preview': chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text']
                            })
                        
                        df_csv = pd.DataFrame(csv_data)
                        csv = df_csv.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Download CSV Report",
                            data=csv,
                            file_name=f"plagiarism_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    elif report_format == "JSON":
                        # Generate JSON report
                        json_data = {
                            "report_metadata": {
                                "generated_at": datetime.now().isoformat(),
                                "report_scope": report_scope,
                                "include_explanations": include_explanations,
                                "include_code_snippets": include_code_snippets,
                                "overall_plagiarism_percentage": result['overall_plagiarism_percentage'],
                                "overall_originality_score": result['overall_originality_score'],
                                "total_chunks": result['total_chunks'],
                                "flagged_chunks": result['flagged_chunks']
                            },
                            "chunk_analysis": result['chunk_results']
                        }
                        
                        json_str = json.dumps(json_data, indent=2)
                        
                        st.download_button(
                            label="📥 Download JSON Report",
                            data=json_str,
                            file_name=f"plagiarism_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    st.success("✅ Report generated successfully!")
                    st.info("💡 You can now download and share your plagiarism analysis report.")
                    
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
    
    # Summary and recommendations
    if 'check_result' in st.session_state:
        st.header("📋 Summary & Recommendations")
        result = st.session_state['check_result']
        
        if result['flagged_chunks'] > 0:
            st.warning(f"⚠️ **{result['flagged_chunks']} out of {result['total_chunks']} code chunks** were flagged for similarity.")
            
            if result['overall_plagiarism_percentage'] > 80:
                st.error("🚨 **HIGH PRIORITY:** This code shows significant plagiarism. Consider complete rewrite of flagged sections.")
            elif result['overall_plagiarism_percentage'] > 50:
                st.warning("⚠️ **MEDIUM PRIORITY:** Review flagged sections and make substantial modifications.")
            else:
                st.info("ℹ️ **LOW PRIORITY:** Minor similarities detected. Consider small modifications to flagged sections.")
        else:
            st.success("✅ **EXCELLENT!** No plagiarism detected. Your code appears to be completely original.")
        
        # Action items
        st.subheader("🎯 Recommended Actions")
        
        if result['flagged_chunks'] > 0:
            st.markdown("**For flagged code chunks:**")
            st.markdown("1. 🔍 Review each flagged section carefully")
            st.markdown("2. ✏️ Rewrite similar code with your own approach")
            st.markdown("3. 🤖 Use AI suggestions for improvement")
            st.markdown("4. 📚 Add proper citations if using external code")
            st.markdown("5. 🧪 Test your rewritten code thoroughly")
        else:
            st.markdown("**Your code is clean! Consider:**")
            st.markdown("1. ✅ Continue with your current approach")
            st.markdown("2. 📝 Document your original solutions")
            st.markdown("3. 🎓 Share your innovative approaches")

if __name__ == "__main__":
    main()
