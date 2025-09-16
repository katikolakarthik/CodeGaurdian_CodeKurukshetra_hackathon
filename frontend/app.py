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
    """Handle file upload and processing."""
    st.header("📁 Upload Code File")
    
    st.subheader("From GitHub Repository:")
    repo_url = st.text_input("GitHub Repo URL (optional)", placeholder="https://github.com/owner/repo or .../tree/branch")
    if st.button("🔗 Fetch Repo & Ingest"):
        if not repo_url.strip():
            st.warning("Please enter a GitHub repository URL.")
        else:
            with st.spinner("Fetching repository and processing code..."):
                try:
                    data = {
                        "repo_url": repo_url,
                        "team_name": st.session_state.get('current_team', 'Team Alpha'),
                        "submission_name": st.session_state.get('current_submission', 'Repo Submission'),
                        "language": "mixed"
                    }
                    response = requests.post(f"{API_BASE_URL}/fetch_repo", data=data)
                    if response.status_code == 200:
                        res = response.json()
                        st.success(f"✅ Ingested repo {res['repo']['owner']}/{res['repo']['name']} with {res['chunk_count']} chunks")
                        st.session_state['upload_result'] = res
                        st.rerun()
                    else:
                        st.error(response.json().get('detail', 'Failed to fetch repo'))
                except Exception as e:
                    st.error(f"Error fetching repo: {e}")

    # File upload
    uploaded_file = st.file_uploader(
        "Choose a code file",
        type=['py', 'java', 'c', 'cpp', 'js', 'ts', 'html', 'css', 'php', 'rb', 'go', 'rs'],
        help="Supported formats: Python, Java, C/C++, JavaScript, TypeScript, HTML, CSS, PHP, Ruby, Go, Rust"
    )
    
    # Code input alternative
    st.subheader("Or paste code directly:")
    code_input = st.text_area(
        "Paste your code here",
        height=200,
        placeholder="def hello_world():\n    print('Hello, World!')"
    )
    
    # Submission details
    col1, col2 = st.columns(2)
    with col1:
        team_name = st.text_input("Team Name", value="Team Alpha")
    with col2:
        submission_name = st.text_input("Submission Name", value="Project Submission")
    
    language = st.selectbox(
        "Programming Language",
        ["python", "java", "c", "cpp", "javascript", "typescript", "html", "css", "php", "ruby", "go", "rust"]
    )
    
    # Submit button
    if st.button("🚀 Upload & Process", type="primary"):
        if uploaded_file or code_input:
            with st.spinner("Processing your code..."):
                try:
                    # Prepare file data
                    if uploaded_file:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                        filename = uploaded_file.name
                    else:
                        # Create a temporary file for code input
                        files = {"file": ("input.txt", code_input.encode(), "text/plain")}
                        filename = "input.txt"
                    
                    data = {
                        "team_name": team_name,
                        "submission_name": submission_name,
                        "language": language
                    }
                    
                    # Upload to backend
                    response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Successfully processed {result['chunk_count']} code chunks!")
                        
                        # Store result in session state
                        st.session_state['upload_result'] = result
                        st.session_state['current_team'] = team_name
                        st.session_state['current_submission'] = submission_name
                        st.session_state['current_language'] = language
                        
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error uploading file: {str(e)}")
        else:
            st.warning("⚠️ Please upload a file or paste code to continue.")

def check_plagiarism():
    """Handle plagiarism checking."""
    st.header("🔍 Check for Plagiarism")
    
    if 'upload_result' not in st.session_state:
        st.warning("⚠️ Please upload a file first in the Upload section.")
        return
    
    # File upload for checking
    uploaded_file = st.file_uploader(
        "Choose a code file to check for plagiarism",
        type=['py', 'java', 'c', 'cpp', 'js', 'ts', 'html', 'css', 'php', 'rb', 'go', 'rs'],
        key="check_file"
    )
    
    # Code input alternative
    st.subheader("Or paste code to check:")
    code_input = st.text_area(
        "Paste code to check",
        height=200,
        key="check_code_input"
    )
    
    # Check button
    if st.button("🔍 Check Plagiarism", type="primary"):
        if uploaded_file or code_input:
            with st.spinner("Analyzing code for plagiarism..."):
                try:
                    # Prepare file data
                    if uploaded_file:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                    else:
                        files = {"file": ("check.txt", code_input.encode(), "text/plain")}
                    
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
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error checking plagiarism: {str(e)}")
        else:
            st.warning("⚠️ Please upload a file or paste code to check.")

def show_results():
    """Display plagiarism check results."""
    st.header("📊 Plagiarism Analysis Results")
    
    if 'check_result' not in st.session_state:
        st.info("ℹ️ No plagiarism check results available. Please check a file first.")
        return
    
    result = st.session_state['check_result']
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Plagiarism %",
            f"{result['overall_plagiarism_percentage']:.1f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            "Originality Score",
            f"{result['overall_originality_score']:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            "Total Chunks",
            result['total_chunks']
        )
    
    with col4:
        st.metric(
            "Flagged Chunks",
            result['flagged_chunks']
        )
    
    # Plagiarism level indicator
    plagiarism_pct = result['overall_plagiarism_percentage']
    if plagiarism_pct > 80:
        st.error("🚨 HIGH PLAGIARISM DETECTED!")
    elif plagiarism_pct > 50:
        st.warning("⚠️ MODERATE SIMILARITY DETECTED")
    elif plagiarism_pct > 20:
        st.info("ℹ️ LOW SIMILARITY DETECTED")
    else:
        st.success("✅ ORIGINAL CODE DETECTED")
    
    # Visualization
    st.subheader("📈 Similarity Distribution")
    
    # Create similarity chart
    chunk_data = []
    for chunk in result['chunk_results']:
        chunk_data.append({
            'Chunk': f"Chunk {chunk['chunk_id'].split('_')[-1]}",
            'Similarity %': chunk['plagiarism_percentage'],
            'Originality %': chunk['originality_score'],
            'Flagged': chunk['is_flagged']
        })
    
    df = pd.DataFrame(chunk_data)
    
    # Bar chart
    fig = px.bar(
        df, 
        x='Chunk', 
        y='Similarity %',
        color='Similarity %',
        color_continuous_scale=['green', 'yellow', 'red'],
        title="Similarity Percentage by Code Chunk"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed results
    st.subheader("🔍 Detailed Analysis")
    
    for i, chunk in enumerate(result['chunk_results']):
        with st.expander(f"Chunk {i+1} - Similarity: {chunk['plagiarism_percentage']:.1f}%", expanded=chunk['is_flagged']):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Your Code:**")
                st.code(chunk['text'], language=st.session_state.get('current_language', 'python'))
            
            with col2:
                if chunk['similar_chunks']:
                    st.markdown("**Most Similar Code:**")
                    similar = chunk['similar_chunks'][0]
                    st.code(similar['metadata']['processed_text'], language=st.session_state.get('current_language', 'python'))
                    st.markdown(f"**Similarity:** {similar['similarity_percentage']:.1f}%")
                    st.markdown(f"**From:** {similar['metadata']['team_name']} - {similar['metadata']['submission_name']}")
                else:
                    st.info("No similar code found")
            
            # Generate explanation if flagged
            if chunk['is_flagged'] and chunk['similar_chunks']:
                if st.button(f"🤖 Generate Explanation for Chunk {i+1}", key=f"explain_{i}"):
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
                                
                                st.markdown("**🤖 AI Explanation:**")
                                st.write(explain_result['explanation'])
                                
                                if explain_result.get('suggestion'):
                                    st.markdown("**💡 Suggestion:**")
                                    st.write(explain_result['suggestion'])
                                
                                if explain_result.get('rewrite_suggestion'):
                                    st.markdown("**✏️ Rewrite Suggestion:**")
                                    st.code(explain_result['rewrite_suggestion']['rewritten_code'], language=st.session_state.get('current_language', 'python'))
                                    
                            else:
                                st.error("Failed to generate explanation")
                                
                        except Exception as e:
                            st.error(f"Error generating explanation: {str(e)}")

def generate_report():
    """Generate and download plagiarism report."""
    st.header("📄 Generate Report")
    
    if 'check_result' not in st.session_state:
        st.warning("⚠️ No plagiarism check results available. Please check a file first.")
        return
    
    result = st.session_state['check_result']
    
    # Report options
    col1, col2 = st.columns(2)
    
    with col1:
        report_format = st.selectbox("Report Format", ["PDF", "CSV", "JSON"])
    
    with col2:
        include_explanations = st.checkbox("Include AI Explanations", value=True)
    
    if st.button("📊 Generate Report", type="primary"):
        with st.spinner("Generating report..."):
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
                    story.append(Paragraph("Summary", styles['Heading2']))
                    summary_data = [
                        ["Metric", "Value"],
                        ["Overall Plagiarism %", f"{result['overall_plagiarism_percentage']:.1f}%"],
                        ["Overall Originality %", f"{result['overall_originality_score']:.1f}%"],
                        ["Total Chunks", str(result['total_chunks'])],
                        ["Flagged Chunks", str(result['flagged_chunks'])],
                        ["Check Time", result['metadata']['check_time']]
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
                    
                    # Detailed results
                    story.append(Paragraph("Detailed Analysis", styles['Heading2']))
                    for i, chunk in enumerate(result['chunk_results']):
                        story.append(Paragraph(f"Chunk {i+1}", styles['Heading3']))
                        story.append(Paragraph(f"Similarity: {chunk['plagiarism_percentage']:.1f}%", styles['Normal']))
                        story.append(Paragraph(f"Originality: {chunk['originality_score']:.1f}%", styles['Normal']))
                        story.append(Paragraph(f"Flagged: {'Yes' if chunk['is_flagged'] else 'No'}", styles['Normal']))
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
                            'Chunk': i+1,
                            'Similarity_%': chunk['plagiarism_percentage'],
                            'Originality_%': chunk['originality_score'],
                            'Flagged': chunk['is_flagged'],
                            'Code_Text': chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text']
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
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")


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
    """Page to compare multiple GitHub repositories and show leaderboard."""
    st.header("🏆 Compare GitHub Repositories")
    st.markdown("Enter two or more GitHub repo URLs (one per line)")
    urls_text = st.text_area("Repository URLs", height=150, placeholder="https://github.com/org/repo1\nhttps://github.com/user/repo2")
    if st.button("🏁 Compare Repos", type="primary"):
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        if len(urls) < 2:
            st.warning("Please enter at least two repository URLs.")
        else:
            with st.spinner("Fetching repositories and computing originality leaderboard..."):
                try:
                    data = {"repo_urls": ",".join(urls)}
                    resp = requests.post(f"{API_BASE_URL}/compare_repos", data=data)
                    if resp.status_code == 200:
                        result = resp.json()
                        st.success("✅ Comparison complete")
                        lb = pd.DataFrame(result['leaderboard'])
                        st.dataframe(lb)
                        import plotly.express as px
                        fig = px.bar(lb, x='repo_url', y='originality_score', title='Originality Leaderboard', color='originality_score', color_continuous_scale=['red','yellow','green'])
                        fig.update_layout(xaxis_tickangle=-30, height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error(resp.json().get('detail', 'Failed to compare repos'))
                except Exception as e:
                    st.error(f"Error comparing repos: {e}")

def main():
    """Main application function."""
    # Header
    st.markdown('<h1 class="main-header">🔍 AI Code Plagiarism Detector</h1>', unsafe_allow_html=True)
    
    # Check API connection
    if not check_api_connection():
        st.error("❌ Backend API is not running. Please start the FastAPI server first.")
        st.code("cd backend && python main.py", language="bash")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Upload Code", "Check Plagiarism", "View Results", "Generate Report", "Code Review", "Compare Repos"]
    )
    
    # Display current status
    if 'upload_result' in st.session_state:
        st.sidebar.success("✅ Code uploaded successfully")
    if 'check_result' in st.session_state:
        st.sidebar.success("✅ Plagiarism check completed")
    
    # Route to appropriate page
    if page == "Upload Code":
        upload_file()
    elif page == "Check Plagiarism":
        check_plagiarism()
    elif page == "View Results":
        show_results()
    elif page == "Generate Report":
        generate_report()
    elif page == "Code Review":
        code_review_page()
    elif page == "Compare Repos":
        compare_repos_page()

if __name__ == "__main__":
    main()
