import os
import yaml
import markdown
from typing import Any

class MarkdownService:
    """Service to parse markdown files with YAML frontmatter for Docs and Blogs."""

    def __init__(self, base_dir: str = "content"):
        self.base_dir = base_dir

    def get_content(self, section: str, slug: str) -> dict[str, Any] | None:
        """Reads a markdown file, parses metadata, and converts markdown body to HTML."""
        file_path = os.path.join(self.base_dir, section, f"{slug}.md")
        
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = {}
            body = content

            # Check if there is YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    # Parse YAML frontmatter
                    metadata = yaml.safe_load(parts[1]) or {}
                    body = parts[2]

            # Convert markdown body to HTML
            html_body = markdown.markdown(body, extensions=["fenced_code", "tables"])

            return {
                "metadata": metadata,
                "html": html_body,
                "slug": slug
            }
        except Exception:
            return None

    def list_posts(self, section: str) -> list[dict[str, Any]]:
        """Lists all files in a section with their frontmatter metadata."""
        dir_path = os.path.join(self.base_dir, section)
        if not os.path.exists(dir_path):
            return []

        posts = []
        for filename in os.listdir(dir_path):
            if filename.endswith(".md"):
                slug = filename[:-3]
                post = self.get_content(section, slug)
                if post:
                    posts.append({
                        "slug": slug,
                        "metadata": post.get("metadata", {}),
                        "title": post.get("metadata", {}).get("title", slug)
                    })
        return posts

markdown_service = MarkdownService()
