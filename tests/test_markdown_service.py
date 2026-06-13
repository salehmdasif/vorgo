import os
from app.services.markdown_service import MarkdownService

def test_markdown_service_parse():
    # Setup a temp markdown file
    os.makedirs("content/test", exist_ok=True)
    temp_file = "content/test/sample.md"
    
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("---\ntitle: Test Title\ndescription: Test Desc\n---\n# Header\nBody content.")

    try:
        service = MarkdownService()
        content = service.get_content("test", "sample")
        
        assert content is not None
        assert content["metadata"]["title"] == "Test Title"
        assert content["metadata"]["description"] == "Test Desc"
        assert "<h1>Header</h1>" in content["html"]
        assert "<p>Body content.</p>" in content["html"]
        
        posts = service.list_posts("test")
        assert len(posts) >= 1
        assert any(p["slug"] == "sample" for p in posts)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists("content/test"):
            os.rmdir("content/test")
