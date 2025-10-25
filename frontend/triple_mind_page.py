"""
TripleMind AI Analysis Page - Frontend for TripleMind AI integration
"""

import streamlit as st
import requests
import json
from datetime import datetime
import tempfile
import os

def triple_mind_page():
    """TripleMind AI Analysis Page"""
    
    st.header("🧠 TripleMind AI Analysis")
    st.markdown("**Comprehensive code analysis using three AI models: Gemini, DeepSeek, and GPT-OSS**")
    
    # Page selection
    page_type = st.radio(
        "Choose analysis type:",
        ["📊 Code Analysis", "💬 General Questions"],
        horizontal=True
    )
    
    if page_type == "📊 Code Analysis":
        code_analysis_page()
    else:
        general_question_page()

def code_analysis_page():
    """Code Analysis Page"""
    
    # API Configuration
    API_BASE_URL = "http://localhost:8000"
    
    # Sidebar for model selection
    with st.sidebar:
        st.subheader("🤖 AI Model Selection")
        
        # Model selection checkboxes
        gemini_enabled = st.checkbox("📚 Gemini (Code-Specific)", value=True, help="Google Gemini for code-specific analysis with citations")
        deepseek_enabled = st.checkbox("🌍 DeepSeek (Global Knowledge)", value=True, help="DeepSeek AI for global programming knowledge")
        gpt_oss_enabled = st.checkbox("🤖 GPT-OSS (High Reasoning)", value=True, help="GPT-OSS-120B for advanced reasoning")
        
        # TripleMind combination options
        st.markdown("**🎯 TripleMind Combinations:**")
        gemini_deepseek = st.checkbox("📚+🌍 Gemini + DeepSeek", value=False, help="Code-specific + Global knowledge")
        gemini_gptoss = st.checkbox("📚+🤖 Gemini + GPT-OSS", value=False, help="Code-specific + High reasoning")
        all_three = st.checkbox("🧠 All Three Minds", value=False, help="Complete TripleMind: Code + Global + Reasoning")
        
        # Ensure only one option is selected
        selected_options = [gemini_enabled, deepseek_enabled, gpt_oss_enabled, gemini_deepseek, gemini_gptoss, all_three]
        if sum(selected_options) > 1:
            st.warning("⚠️ Please select only one option")
            return
        elif sum(selected_options) == 0:
            # Default to all three
            all_three = True
        
        # Determine models to use
        if all_three:
            models = "gemini,deepseek,gpt_oss"
        elif gemini_deepseek:
            models = "gemini,deepseek"
        elif gemini_gptoss:
            models = "gemini,gpt_oss"
        elif gemini_enabled:
            models = "gemini"
        elif deepseek_enabled:
            models = "deepseek"
        elif gpt_oss_enabled:
            models = "gpt_oss"
        else:
            models = "gemini,deepseek,gpt_oss"
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Ask Questions About Your Code")
        
        # Question input
        question = st.text_area(
            "Ask a question:",
            placeholder="e.g., What are the potential security vulnerabilities in this code?",
            help="Ask any question about your code - get comprehensive AI analysis!"
        )
        
        # Input method selection
        st.subheader("📁 Code Input Method")
        input_method = st.radio(
            "Choose how to provide your code:",
            ["📄 Upload File", "📝 Paste Code", "🔗 GitHub Repository"],
            horizontal=True
        )
        
        uploaded_file = None
        code_input = None
        repo_url = None
        
        if input_method == "📄 Upload File":
            uploaded_file = st.file_uploader(
                "Upload a code file:",
                type=['py', 'js', 'java', 'cpp', 'c', 'html', 'css', 'php', 'rb', 'go', 'rs'],
                help="Upload your code file for analysis"
            )
        
        elif input_method == "📝 Paste Code":
            code_input = st.text_area(
                "Paste your code here:",
                height=200,
                help="Paste your code directly for analysis"
            )
        
        elif input_method == "🔗 GitHub Repository":
            repo_url = st.text_input(
                "GitHub Repository URL:",
                placeholder="https://github.com/username/repository",
                help="Enter the GitHub repository URL to analyze"
            )
        
        # Analysis options
        st.subheader("⚙️ Analysis Options")
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            team_name = st.text_input("Team Name:", value="TripleMind Team")
        
        with col_opt2:
            submission_name = st.text_input("Submission Name:", value="TripleMind Analysis")
        
        # Analyze button
        if st.button("🚀 Analyze with TripleMind", type="primary", disabled=not question):
            if not question:
                st.error("Please enter a question to analyze.")
                return
            
            # Validate input
            if input_method == "📄 Upload File" and not uploaded_file:
                st.error("Please upload a file.")
                return
            elif input_method == "📝 Paste Code" and not code_input:
                st.error("Please paste your code.")
                return
            elif input_method == "🔗 GitHub Repository" and not repo_url:
                st.error("Please enter a GitHub repository URL.")
                return
            
            # Prepare request data
            files = {}
            data = {
                'question': question,
                'models': models,
                'team_name': team_name,
                'submission_name': submission_name
            }
            
            if uploaded_file:
                files['file'] = (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
            elif code_input:
                data['code'] = code_input
            elif repo_url:
                data['repo_url'] = repo_url
            
            # Show progress
            with st.spinner("🧠 TripleMind AI is analyzing..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/triple_mind_analyze",
                        data=data,
                        files=files,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display results
                        st.success("✅ TripleMind Analysis Complete!")
                        
                        # Show model indicators
                        models_used = result.get('models_used', [])
                        if len(models_used) == 3:
                            st.success("🧠 **TripleMind Complete:** Code + Global + Reasoning")
                        elif len(models_used) == 2:
                            st.success(f"🎯 **Dual Analysis:** {' + '.join(models_used)}")
                        else:
                            st.info(f"🤖 **Single Model:** {models_used[0] if models_used else 'Unknown'}")
                        
                        # Display combined response
                        st.subheader("📊 Analysis Results")
                        combined_response = result.get('combined_response', '')
                        if combined_response:
                            st.markdown(combined_response)
                        
                        # Display individual responses
                        responses = result.get('responses', {})
                        if responses:
                            st.subheader("🔍 Individual AI Responses")
                            
                            for model, response_text in responses.items():
                                with st.expander(f"🤖 {model.upper()} Response"):
                                    st.markdown(response_text)
                        
                        # Display citations if available
                        citations = result.get('citations', [])
                        if citations:
                            st.subheader("📚 Code Citations")
                            for citation in citations:
                                st.write(f"📄 **{citation['file']}** - Line {citation['line']}")
                                if citation.get('count', 1) > 1:
                                    st.caption(f"Referenced {citation['count']} times")
                        
                        # Store in session state for history
                        if 'triple_mind_history' not in st.session_state:
                            st.session_state.triple_mind_history = []
                        
                        st.session_state.triple_mind_history.append({
                            'question': question,
                            'response': combined_response,
                            'models_used': models_used,
                            'timestamp': datetime.now().strftime("%H:%M"),
                            'input_method': input_method
                        })
                        
                    else:
                        st.error(f"❌ Analysis failed: {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")
    
    with col2:
        st.subheader("📊 TripleMind Features")
        
        # Model descriptions
        st.markdown("**🤖 AI Models:**")
        st.write("• **📚 Gemini**: Code-specific analysis with citations")
        st.write("• **🌍 DeepSeek**: Global programming knowledge")
        st.write("• **🤖 GPT-OSS**: High-reasoning capabilities")
        
        st.markdown("---")
        
        # Analysis types
        st.markdown("**🔍 Analysis Types:**")
        st.write("• Security vulnerabilities")
        st.write("• Code optimization")
        st.write("• Bug detection")
        st.write("• Best practices")
        st.write("• Performance analysis")
        
        st.markdown("---")
        
        # History
        if 'triple_mind_history' in st.session_state and st.session_state.triple_mind_history:
            st.subheader("📝 Recent Analysis")
            for i, analysis in enumerate(reversed(st.session_state.triple_mind_history[-3:])):
                with st.expander(f"Q: {analysis['question'][:30]}... ({analysis['timestamp']})"):
                    st.write(f"**Question:** {analysis['question']}")
                    st.markdown(analysis['response'])
                    st.caption(f"Models: {', '.join(analysis['models_used'])}")
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.triple_mind_history = []
            st.experimental_rerun()

def general_question_page():
    """General Question Page - Ask questions without code context"""
    
    st.header("💬 General AI Questions")
    st.markdown("**Ask general programming questions using TripleMind AI models**")
    
    # API Configuration
    API_BASE_URL = "http://localhost:8000"
    
    # Sidebar for model selection
    with st.sidebar:
        st.subheader("🤖 AI Model Selection")
        
        # Model selection checkboxes
        gemini_enabled = st.checkbox("📚 Gemini", value=True, help="Google Gemini for general knowledge")
        deepseek_enabled = st.checkbox("🌍 DeepSeek", value=True, help="DeepSeek AI for global knowledge")
        gpt_oss_enabled = st.checkbox("🤖 GPT-OSS", value=True, help="GPT-OSS-120B for high reasoning")
        
        # TripleMind combination options
        st.markdown("**🎯 TripleMind Combinations:**")
        gemini_deepseek = st.checkbox("📚+🌍 Gemini + DeepSeek", value=False, help="General + Global knowledge")
        gemini_gptoss = st.checkbox("📚+🤖 Gemini + GPT-OSS", value=False, help="General + High reasoning")
        all_three = st.checkbox("🧠 All Three Minds", value=False, help="Complete TripleMind: General + Global + Reasoning")
        
        # Ensure only one option is selected
        selected_options = [gemini_enabled, deepseek_enabled, gpt_oss_enabled, gemini_deepseek, gemini_gptoss, all_three]
        if sum(selected_options) > 1:
            st.warning("⚠️ Please select only one option")
            return
        elif sum(selected_options) == 0:
            # Default to all three
            all_three = True
        
        # Determine models to use
        if all_three:
            models = "gemini,deepseek,gpt_oss"
        elif gemini_deepseek:
            models = "gemini,deepseek"
        elif gemini_gptoss:
            models = "gemini,gpt_oss"
        elif gemini_enabled:
            models = "gemini"
        elif deepseek_enabled:
            models = "deepseek"
        elif gpt_oss_enabled:
            models = "gpt_oss"
        else:
            models = "gemini,deepseek,gpt_oss"
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Question input
        question = st.text_area(
            "Ask a general programming question:",
            placeholder="e.g., What are the best practices for writing secure Python code?",
            height=100,
            help="Ask any general programming question"
        )
        
        # Ask button
        if st.button("🚀 Ask TripleMind", type="primary", disabled=not question):
            if not question:
                st.error("Please enter a question.")
                return
            
            # Prepare request data
            data = {
                'question': question,
                'models': models
            }
            
            # Show progress
            with st.spinner("🧠 TripleMind AI is thinking..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/triple_mind_question",
                        data=data,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display results
                        st.success("✅ TripleMind Response Complete!")
                        
                        # Show model indicators
                        models_used = result.get('models_used', [])
                        if len(models_used) == 3:
                            st.success("🧠 **TripleMind Complete:** General + Global + Reasoning")
                        elif len(models_used) == 2:
                            st.success(f"🎯 **Dual Response:** {' + '.join(models_used)}")
                        else:
                            st.info(f"🤖 **Single Model:** {models_used[0] if models_used else 'Unknown'}")
                        
                        # Display combined response
                        st.subheader("📊 AI Response")
                        combined_response = result.get('combined_response', '')
                        if combined_response:
                            st.markdown(combined_response)
                        
                        # Display individual responses
                        responses = result.get('responses', {})
                        if responses:
                            st.subheader("🔍 Individual AI Responses")
                            
                            for model, response_text in responses.items():
                                with st.expander(f"🤖 {model.upper()} Response"):
                                    st.markdown(response_text)
                        
                        # Store in session state for history
                        if 'general_question_history' not in st.session_state:
                            st.session_state.general_question_history = []
                        
                        st.session_state.general_question_history.append({
                            'question': question,
                            'response': combined_response,
                            'models_used': models_used,
                            'timestamp': datetime.now().strftime("%H:%M")
                        })
                        
                    else:
                        st.error(f"❌ Question failed: {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Question error: {str(e)}")
    
    with col2:
        st.subheader("💡 Question Examples")
        
        st.markdown("**🔍 Code Analysis:**")
        st.write("• How can I optimize this algorithm?")
        st.write("• What security issues exist here?")
        st.write("• How to improve code readability?")
        
        st.markdown("**📚 Learning:**")
        st.write("• Explain design patterns")
        st.write("• Best practices for Python")
        st.write("• How to debug effectively?")
        
        st.markdown("**🚀 Career:**")
        st.write("• Software engineering skills")
        st.write("• Interview preparation")
        st.write("• Technology trends")
        
        # History
        if 'general_question_history' in st.session_state and st.session_state.general_question_history:
            st.markdown("---")
            st.subheader("📝 Recent Questions")
            for i, qa in enumerate(reversed(st.session_state.general_question_history[-3:])):
                with st.expander(f"Q: {qa['question'][:30]}... ({qa['timestamp']})"):
                    st.write(f"**Question:** {qa['question']}")
                    st.markdown(qa['response'])
                    st.caption(f"Models: {', '.join(qa['models_used'])}")
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.general_question_history = []
            st.experimental_rerun()