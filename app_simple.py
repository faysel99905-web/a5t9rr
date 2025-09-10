from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

# Simple HTML template
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>a5t9r.com - Universal Document QA & Summarizer</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --text-color: #333333;
            --container-bg: #f8f9fa;
            --button-bg: #007bff;
            --input-border: #ced4da;
            --input-bg: #ffffff;
            --shadow: rgba(0,0,0,0.1);
        }

        [data-theme="dark"] {
            --bg-color: #1a1a1a;
            --text-color: #ffffff;
            --container-bg: #2d2d2d;
            --button-bg: #0d6efd;
            --input-border: #495057;
            --input-bg: #343a40;
            --shadow: rgba(0,0,0,0.3);
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
        
        input[type="text"], textarea {
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
        
        textarea {
            height: 100px;
            resize: vertical;
        }
        
        input[type="submit"] {
            background-color: var(--button-bg);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        
        input[type="submit"]:hover {
            opacity: 0.9;
        }
        
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            background-color: var(--container-bg);
            border-left: 4px solid var(--button-bg);
            white-space: pre-line;
        }
        
        .error {
            background-color: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }
        
        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--button-bg);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 2px 10px var(--shadow);
            transition: all 0.3s ease;
        }
        
        .theme-toggle:hover {
            transform: scale(1.1);
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid var(--input-border);
            color: var(--text-color);
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle Dark/Light Theme">
        🌙
    </button>
    
    <div class="container">
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="margin: 0; color: var(--text-color);">📄 a5t9r.com - Universal Document QA & Summarizer</h1>
        </div>
        
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label for="text">📝 Enter your document text:</label>
                <textarea name="text" id="text" placeholder="Paste your document text here... (PDF, Word, Excel content)"></textarea>
            </div>
            
            <div class="form-group">
                <label for="question">❓ Ask a question about the document:</label>
                <input type="text" name="question" id="question" placeholder="What is the main topic? What are the key points?">
            </div>
            
            <div class="form-group">
                <label for="action">🎯 Choose action:</label>
                <select name="action" id="action" style="width: 100%; padding: 10px; border: 2px solid var(--input-border); border-radius: 5px; background-color: var(--input-bg); color: var(--text-color);">
                    <option value="qa">Question & Answer</option>
                    <option value="summary">Document Summary</option>
                </select>
            </div>
            
            <input type="submit" value="🚀 Process Document">
        </form>
        
        {% if result %}
        <div class="result">{{ result }}</div>
        {% endif %}
        
        {% if error %}
        <div class="result error">{{ error }}</div>
        {% endif %}
    </div>
    
    <div class="footer">
        <p><strong>a5t9r</strong> - Universal Document QA & Summarizer</p>
        <p>© 2024 Faisal 24. All rights reserved.</p>
        <p>Powered by AI • Built with Python & Flask</p>
    </div>

    <script>
        function toggleTheme() {
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update button icon
            const button = document.querySelector('.theme-toggle');
            button.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        }
        
        function loadTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.body.setAttribute('data-theme', savedTheme);
            
            // Update button icon
            const button = document.querySelector('.theme-toggle');
            button.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
        }
        
        document.addEventListener('DOMContentLoaded', loadTheme);
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    
    if request.method == "POST":
        try:
            text = request.form.get("text", "").strip()
            question = request.form.get("question", "").strip()
            action = request.form.get("action", "qa")
            
            if not text:
                error = "Please enter some document text."
            elif action == "qa" and not question:
                error = "Please enter a question for Q&A mode."
            else:
                if action == "qa":
                    # Simple keyword-based Q&A
                    result = f"📋 Question: {question}\n\n💡 Answer: Based on the document content:\n\n"
                    
                    # Simple search for keywords
                    question_lower = question.lower()
                    text_lower = text.lower()
                    
                    # Look for relevant sentences
                    sentences = text.split('.')
                    relevant_sentences = []
                    
                    for sentence in sentences:
                        if any(word in sentence.lower() for word in question_lower.split()):
                            relevant_sentences.append(sentence.strip())
                    
                    if relevant_sentences:
                        result += "Relevant information found:\n"
                        for i, sentence in enumerate(relevant_sentences[:3]):
                            result += f"• {sentence}\n"
                    else:
                        result += "No specific information found for your question. Here's a preview of the document:\n\n"
                        result += text[:500] + "..." if len(text) > 500 else text
                    
                    result += f"\n\n📊 Document contains {len(text.split())} words and {len(text.split('.'))} sentences."
                
                elif action == "summary":
                    # Simple text summarization
                    sentences = text.split('.')
                    if len(sentences) <= 3:
                        result = f"📝 Summary:\n\n{text}\n\n📊 Original: {len(text.split())} words"
                    else:
                        # Take first few sentences as summary
                        summary_sentences = sentences[:3]
                        summary = '. '.join(summary_sentences) + '.'
                        result = f"📝 Summary:\n\n{summary}\n\n📊 Original: {len(text.split())} words"
                
        except Exception as e:
            error = f"An error occurred: {str(e)}"
    
    return render_template_string(HTML, result=result, error=error)

if __name__ == "__main__":
    print("🚀 Starting a5t9r - Universal Document QA & Summarizer...")
    print("📄 Simple text-based document processing")
    print("👨‍💻 Created by Faisal 24")
    print("🌐 Open http://127.0.0.1:5000 in your browser")
    
    # Get port from environment variable (for Render) or use 5000 for local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
