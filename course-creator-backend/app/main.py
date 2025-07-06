from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import markdown
import os
from datetime import datetime

app = FastAPI(
    title="Course Creator API",
    description="Backend API for Course Creator Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Course Creator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Course Creator API is running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/docs", response_class=HTMLResponse)
async def get_documentation():
    """Serve the documentation as HTML"""
    try:
        # Get the path to docs directory
        docs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "README.md")
        
        # Read the markdown file
        with open(docs_path, "r", encoding="utf-8") as file:
            markdown_content = file.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content, 
            extensions=['codehilite', 'fenced_code', 'toc', 'tables']
        )
        
        # Wrap in a nice HTML template
        full_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Course Creator Documentation</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8fafc;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                h1 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
                h2 {{ color: #1e40af; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }}
                h3 {{ color: #1d4ed8; }}
                code {{
                    background: #f1f5f9;
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
                }}
                pre {{
                    background: #1e293b;
                    color: #e2e8f0;
                    padding: 20px;
                    border-radius: 8px;
                    overflow-x: auto;
                }}
                pre code {{
                    background: none;
                    padding: 0;
                    color: inherit;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div style="text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; border-radius: 12px;">
                    <h1 style="color: white; border: none; margin: 0;">📚 Course Creator Documentation</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Complete API and Development Guide</p>
                </div>
                {html_content}
                <hr style="margin: 40px 0;">
                <footer style="text-align: center; color: #64748b; font-size: 14px;">
                    Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
                    <a href="/health" style="color: #2563eb;">API Health</a> | 
                    <a href="/" style="color: #2563eb;">API Root</a>
                </footer>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=full_html)
        
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
                    <h1 style="color: #dc2626;">Documentation Not Found</h1>
                    <p>The documentation file could not be loaded.</p>
                    <p><a href="/health">Check API Health</a></p>
                </body>
            </html>
            """,
            status_code=404
        )

@app.get("/api/courses")
async def get_courses():
    """Get all courses (placeholder)"""
    return {
        "success": True,
        "data": [
            {
                "id": "1",
                "title": "Introduction to Web Development",
                "description": "Learn HTML, CSS, and JavaScript basics",
                "instructor": "John Doe",
                "price": 99.00,
                "difficulty": "beginner"
            },
            {
                "id": "2", 
                "title": "Advanced React Development",
                "description": "Master React hooks and advanced patterns",
                "instructor": "Jane Smith",
                "price": 149.00,
                "difficulty": "advanced"
            }
        ],
        "message": "Courses retrieved successfully"
    }
