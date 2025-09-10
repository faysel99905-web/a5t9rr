from flask import Flask, request, render_template_string
from transformers import pipeline
from PIL import Image
import pytesseract
import os
import io
import PyPDF2
import pandas as pd
from docx import Document
import tempfile

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize pipelines
qa_pipeline = pipeline("document-question-answering", model="impira/layoutlm-document-qa")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

app = Flask(__name__)

# HTML template
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>a5t9r.com - Universal Document QA & Summarizer</title>
  <style>
    :root {
      --bg-color: #f5f5f5;
      --container-bg: white;
      --text-color: #333;
      --border-color: #ddd;
      --shadow: rgba(0,0,0,0.1);
      --input-bg: white;
      --input-border: #ddd;
      --button-bg: #007bff;
      --button-hover: #0056b3;
      --answer-bg: #e8f5e8;
      --answer-border: #28a745;
      --summary-bg: #e3f2fd;
      --summary-border: #2196f3;
      --error-bg: #f8d7da;
      --error-border: #dc3545;
      --info-bg: #fff3cd;
      --info-border: #ffc107;
      --tab-bg: #f8f9fa;
      --tab-border: #dee2e6;
      --tab-active-bg: #007bff;
    }

    [data-theme="dark"] {
      --bg-color: #1a1a1a;
      --container-bg: #2d2d2d;
      --text-color: #e0e0e0;
      --border-color: #444;
      --shadow: rgba(0,0,0,0.3);
      --input-bg: #3d3d3d;
      --input-border: #555;
      --button-bg: #0d6efd;
      --button-hover: #0b5ed7;
      --answer-bg: #1e4d2b;
      --answer-border: #28a745;
      --summary-bg: #1a365d;
      --summary-border: #2196f3;
      --error-bg: #4a1a1a;
      --error-border: #dc3545;
      --info-bg: #4a3c1a;
      --info-border: #ffc107;
      --tab-bg: #3d3d3d;
      --tab-border: #555;
      --tab-active-bg: #0d6efd;
    }

    body {
      font-family: Arial, sans-serif;
      max-width: 1000px;
      margin: 0 auto;
      padding: 20px;
      background-color: var(--bg-color);
      color: var(--text-color);
      transition: background-color 0.3s ease, color 0.3s ease;
    }
    .container {
      background-color: var(--container-bg);
      padding: 30px;
      border-radius: 10px;
      box-shadow: 0 2px 10px var(--shadow);
      transition: background-color 0.3s ease, box-shadow 0.3s ease;
    }
    h1 {
      color: var(--text-color);
      text-align: center;
      margin-bottom: 30px;
    }
    .form-group {
      margin-bottom: 20px;
    }
    label {
      display: block;
      margin-bottom: 5px;
      font-weight: bold;
      color: var(--text-color);
    }
    input[type="file"], input[type="text"], select {
      width: 100%;
      padding: 10px;
      border: 2px solid var(--input-border);
      border-radius: 5px;
      font-size: 16px;
      box-sizing: border-box;
      background-color: var(--input-bg);
      color: var(--text-color);
      transition: border-color 0.3s ease, background-color 0.3s ease;
    }
    input[type="submit"] {
      background-color: var(--button-bg);
      color: white;
      padding: 12px 30px;
      border: none;
      border-radius: 5px;
      font-size: 16px;
      cursor: pointer;
      width: 100%;
      margin-top: 10px;
      transition: background-color 0.3s ease;
    }
    input[type="submit"]:hover {
      background-color: var(--button-hover);
    }
    .answer {
      background-color: var(--answer-bg);
      padding: 20px;
      border-radius: 5px;
      border-left: 4px solid var(--answer-border);
      margin-top: 20px;
      transition: background-color 0.3s ease;
    }
    .answer h2 {
      color: var(--answer-border);
      margin-top: 0;
    }
    .summary {
      background-color: var(--summary-bg);
      padding: 20px;
      border-radius: 5px;
      border-left: 4px solid var(--summary-border);
      margin-top: 20px;
      transition: background-color 0.3s ease;
    }
    .summary h2 {
      color: var(--summary-border);
      margin-top: 0;
    }
    .error {
      background-color: var(--error-bg);
      color: var(--text-color);
      padding: 15px;
      border-radius: 5px;
      border-left: 4px solid var(--error-border);
      margin-top: 20px;
      transition: background-color 0.3s ease;
    }
    .file-info {
      background-color: var(--info-bg);
      padding: 15px;
      border-radius: 5px;
      border-left: 4px solid var(--info-border);
      margin-top: 20px;
      transition: background-color 0.3s ease;
    }
    .file-info h3 {
      color: var(--text-color);
      margin-top: 0;
    }
    .tabs {
      display: flex;
      margin-bottom: 20px;
    }
    .tab {
      flex: 1;
      padding: 10px;
      text-align: center;
      background-color: var(--tab-bg);
      border: 1px solid var(--tab-border);
      cursor: pointer;
      border-radius: 5px 5px 0 0;
      color: var(--text-color);
      transition: background-color 0.3s ease, color 0.3s ease;
    }
    .tab.active {
      background-color: var(--tab-active-bg);
      color: white;
    }
    .tab-content {
      display: none;
    }
    .tab-content.active {
      display: block;
    }
    .theme-toggle {
      position: fixed;
      top: 20px;
      right: 20px;
      background-color: var(--button-bg);
      color: white;
      border: none;
      border-radius: 50%;
      width: 50px;
      height: 50px;
      font-size: 20px;
      cursor: pointer;
      box-shadow: 0 2px 10px var(--shadow);
      transition: background-color 0.3s ease, transform 0.2s ease;
      z-index: 1000;
    }
    .theme-toggle:hover {
      background-color: var(--button-hover);
      transform: scale(1.1);
    }
  </style>
</head>
<body>
  <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Dark/Light Theme">
    🌙
  </button>
  
  <div class="container">
    <div style="text-align: center; margin-bottom: 20px;">
      <h1 style="margin: 0; color: var(--text-color);">📄 Universal Document QA & Summarizer</h1>
    </div>
    
    <div class="tabs">
      <div class="tab active" onclick="showTab('qa')">Question & Answer</div>
      <div class="tab" onclick="showTab('summary')">Document Summary</div>
    </div>

    <div id="qa-tab" class="tab-content active">
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="qa">
        <div class="form-group">
          <label for="file">Upload Document:</label>
          <input type="file" name="file" accept=".pdf,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg,.gif,.bmp,.tiff" required>
          <small style="color: #666; font-size: 12px; margin-top: 5px; display: block;">
            📁 Supported formats: PDF, Excel (.xlsx, .xls), Word (.docx, .doc), Images (.png, .jpg, .jpeg, .gif, .bmp, .tiff)
          </small>
        </div>
        <div class="form-group">
          <label for="question">Ask a question:</label>
          <input type="text" name="question" required placeholder="e.g., What is the main topic? What are the key findings?">
          <small style="color: #666; font-size: 12px; margin-top: 5px; display: block;">
            💡 Try asking: "What is the main topic?", "What are the key findings?", "What is the total amount?", "Who is the author?"
          </small>
        </div>
        <input type="submit" value="Ask Question">
      </form>
    </div>

    <div id="summary-tab" class="tab-content">
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="summary">
        <div class="form-group">
          <label for="file">Upload Document:</label>
          <input type="file" name="file" accept=".pdf,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg,.gif,.bmp,.tiff" required>
          <small style="color: #666; font-size: 12px; margin-top: 5px; display: block;">
            📁 Supported formats: PDF, Excel (.xlsx, .xls), Word (.docx, .doc), Images (.png, .jpg, .jpeg, .gif, .bmp, .tiff)
          </small>
        </div>
        <div class="form-group">
          <label for="summary_type">Summary Type:</label>
          <select name="summary_type">
            <option value="short">Short Summary (2-3 sentences)</option>
            <option value="medium">Medium Summary (4-6 sentences)</option>
            <option value="long">Long Summary (7-10 sentences)</option>
          </select>
        </div>
        <input type="submit" value="Generate Summary">
      </form>
    </div>

    {% if file_info %}
    <div class="file-info">
      <h3>📋 File Information:</h3>
      <p><strong>File Name:</strong> {{ file_info.name }}</p>
      <p><strong>File Type:</strong> {{ file_info.type }}</p>
      <p><strong>File Size:</strong> {{ file_info.size }}</p>
      {% if file_info.pages %}
      <p><strong>Pages:</strong> {{ file_info.pages }}</p>
      {% endif %}
      {% if file_info.sheets %}
      <p><strong>Excel Sheets:</strong> {{ file_info.sheets }}</p>
      {% endif %}
    </div>
    {% endif %}

    {% if answer %}
    <div class="answer">
      <h2>💡 Answer:</h2>
      <div style="white-space: pre-line; line-height: 1.6;">{{ answer }}</div>
    </div>
    {% endif %}

    {% if summary %}
    <div class="summary">
      <h2>📝 Document Summary:</h2>
      <div style="white-space: pre-line; line-height: 1.6;">{{ summary }}</div>
    </div>
    {% endif %}

    {% if error %}
    <div class="error">
      <h3>❌ Error:</h3>
      <p>{{ error }}</p>
    </div>
    {% endif %}
  </div>

  <!-- Footer -->
  <footer style="text-align: center; margin-top: 40px; padding: 20px; color: var(--text-color); border-top: 1px solid var(--border-color);">
    <div style="margin-bottom: 10px;">
      <h3 style="color: var(--button-bg); margin: 0; font-size: 24px; font-weight: bold;">a5t9r</h3>
      <p style="margin: 5px 0; font-size: 14px; opacity: 0.8;">Universal Document QA & Summarizer</p>
    </div>
    <div style="font-size: 12px; opacity: 0.7;">
      <p style="margin: 0;">© 2024 Faisal 24. All rights reserved.</p>
      <p style="margin: 5px 0 0 0;">Powered by AI • Built with Python & Flask</p>
    </div>
  </footer>

  <script>
    // Theme management
    function toggleTheme() {
      const body = document.body;
      const themeToggle = document.querySelector('.theme-toggle');
      const currentTheme = body.getAttribute('data-theme');
      
      if (currentTheme === 'dark') {
        body.removeAttribute('data-theme');
        themeToggle.textContent = '🌙';
        localStorage.setItem('theme', 'light');
      } else {
        body.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
      }
    }
    
    // Load saved theme on page load
    function loadTheme() {
      const savedTheme = localStorage.getItem('theme');
      const themeToggle = document.querySelector('.theme-toggle');
      
      if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️';
      } else {
        themeToggle.textContent = '🌙';
      }
    }
    
    // Tab management
    function showTab(tabName) {
      // Hide all tab contents
      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
      });
      
      // Remove active class from all tabs
      document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
      });
      
      // Show selected tab content
      document.getElementById(tabName + '-tab').classList.add('active');
      
      // Add active class to clicked tab
      event.target.classList.add('active');
    }
    
    // Initialize theme on page load
    document.addEventListener('DOMContentLoaded', loadTheme);
  </script>
</body>
</html>
"""

def extract_text_from_pdf(file_stream):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        text = ""
        pages = len(pdf_reader.pages)
        
        for page_num in range(pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        return text, pages
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def extract_text_from_excel(file_stream):
    """Extract text from Excel file"""
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_stream)
        text = ""
        sheet_names = excel_file.sheet_names
        
        for sheet_name in sheet_names:
            df = pd.read_excel(file_stream, sheet_name=sheet_name)
            text += f"\n--- Sheet: {sheet_name} ---\n"
            text += df.to_string(index=False) + "\n"
        
        return text, sheet_names
    except Exception as e:
        raise Exception(f"Error reading Excel file: {str(e)}")

def extract_text_from_word(file_stream):
    """Extract text from Word document"""
    try:
        doc = Document(file_stream)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text
    except Exception as e:
        raise Exception(f"Error reading Word document: {str(e)}")

def extract_text_from_image(file_stream):
    """Extract text from image using OCR"""
    try:
        image = Image.open(file_stream)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise Exception(f"Error reading image: {str(e)}")

def get_file_info(file):
    """Get file information"""
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    size_mb = size / (1024 * 1024)
    if size_mb < 1:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size_mb:.1f} MB"
    
    return {
        'name': file.filename,
        'size': size_str,
        'type': file.content_type or 'Unknown'
    }

def process_document(file_stream, filename):
    """Process document and extract text based on file type"""
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if file_ext == 'pdf':
        text, pages = extract_text_from_pdf(file_stream)
        return text, {'pages': pages}
    elif file_ext in ['xlsx', 'xls']:
        text, sheets = extract_text_from_excel(file_stream)
        return text, {'sheets': sheets}
    elif file_ext in ['docx', 'doc']:
        text = extract_text_from_word(file_stream)
        return text, {}
    elif file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
        text = extract_text_from_image(file_stream)
        return text, {}
    else:
        raise Exception(f"Unsupported file format: {file_ext}")

def generate_summary(text, summary_type="medium"):
    """Generate summary of the text"""
    try:
        # Limit text length for summarization
        max_length = 1024
        if len(text) > max_length:
            text = text[:max_length]
        
        # Adjust max_length based on summary type
        if summary_type == "short":
            max_length = 50
        elif summary_type == "medium":
            max_length = 100
        else:  # long
            max_length = 150
        
        summary = summarizer(text, max_length=max_length, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")

@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    summary = None
    file_info = None
    error = None
    
    if request.method == "POST":
        try:
            file = request.files["file"]
            action = request.form.get("action", "qa")
            
            if not file or not file.filename:
                error = "Please select a valid file."
            else:
                # Get file info
                file_info = get_file_info(file)
                
                # Reset file stream
                file.stream.seek(0)
                
                # Process document
                text, extra_info = process_document(file.stream, file.filename)
                file_info.update(extra_info)
                
                if action == "qa":
                    question = request.form.get("question", "").strip()
                    if not question:
                        error = "Please enter a question."
                    else:
                        # For text-based documents, we'll use a different approach
                        # since the document QA pipeline is designed for images
                        if len(text.strip()) == 0:
                            error = "No text could be extracted from the document."
                        else:
                            # Simple keyword-based answer for text documents
                            answer = f"📋 Question: {question}\n\n💡 Answer: Based on the document content, here's what I found:\n\n"
                            
                            # Simple search for keywords in the text
                            question_lower = question.lower()
                            text_lower = text.lower()
                            
                            # Look for relevant sentences
                            sentences = text.split('.')
                            relevant_sentences = []
                            
                            for sentence in sentences:
                                if any(word in sentence.lower() for word in question_lower.split()):
                                    relevant_sentences.append(sentence.strip())
                            
                            if relevant_sentences:
                                answer += "Relevant information found:\n"
                                for i, sentence in enumerate(relevant_sentences[:3]):
                                    answer += f"• {sentence}\n"
                            else:
                                answer += "No specific information found for your question. Here's a preview of the document content:\n\n"
                                answer += text[:500] + "..." if len(text) > 500 else text
                            
                            answer += f"\n\n📊 Document contains {len(text.split())} words and {len(text.split('.'))} sentences."
                
                elif action == "summary":
                    summary_type = request.form.get("summary_type", "medium")
                    if len(text.strip()) == 0:
                        error = "No text could be extracted from the document."
                    else:
                        summary = generate_summary(text, summary_type)
                        summary = f"📝 Summary Type: {summary_type.title()}\n\n{summary}\n\n📊 Original document: {len(text.split())} words"
                
        except Exception as e:
            error = f"An error occurred: {str(e)}"
    
    return render_template_string(HTML, answer=answer, summary=summary, file_info=file_info, error=error)

if __name__ == "__main__":
    print("🚀 Starting a5t9r - Universal Document QA & Summarizer...")
    print("📄 Supports: PDF, Excel, Word, Images")
    print("👨‍💻 Created by Faisal 24")
    print("🌐 Open http://127.0.0.1:5000 in your browser")
    
    # Get port from environment variable (for Heroku) or use 5000 for local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)