import io
import json
import csv
from typing import Dict, Any, List, Optional
import pypdf

class DocumentProcessor:
    """Processes, extracts, and sanitizes uploaded knowledge documents."""

    SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md", ".csv", ".json"]

    @classmethod
    def process_file_content(cls, file_name: str, content_bytes: bytes) -> Dict[str, Any]:
        """
        Extract clean text content from file bytes based on file extension.
        Returns: {"success": bool, "extracted_text": str, "metadata": dict, "error": str}
        """
        lower_name = file_name.lower()
        extracted_text = ""
        metadata = {"file_name": file_name, "size_bytes": len(content_bytes)}

        try:
            if lower_name.endswith(".pdf"):
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                pages = []
                for idx, page in enumerate(reader.pages):
                    t = page.extract_text()
                    if t:
                        pages.append(t)
                extracted_text = "\n".join(pages)
                metadata["page_count"] = len(reader.pages)

            elif lower_name.endswith(".txt") or lower_name.endswith(".md"):
                extracted_text = content_bytes.decode("utf-8", errors="replace")

            elif lower_name.endswith(".csv"):
                decoded = content_bytes.decode("utf-8", errors="replace")
                reader = csv.reader(io.StringIO(decoded))
                rows = [", ".join(row) for row in reader]
                extracted_text = "\n".join(rows)
                metadata["row_count"] = len(rows)

            elif lower_name.endswith(".json"):
                decoded = content_bytes.decode("utf-8", errors="replace")
                parsed = json.loads(decoded)
                extracted_text = json.dumps(parsed, indent=2)

            else:
                return {
                    "success": False,
                    "error": f"Unsupported file extension. Allowed: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
                }

            # Sanitize extracted text: remove dangerous script tags
            clean_text = extracted_text.replace("<script", "&lt;script").replace("</script>", "&lt;/script&gt;")

            return {
                "success": True,
                "extracted_text": clean_text.strip(),
                "metadata": metadata
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to extract text: {str(e)}"}
