import asyncio
import os
import re
from pathlib import Path

from mcp_server import create_faiss_index, list_dir, read_file


async def find_md_files(path: str = ".") -> list[str]:
    """Recursively find all .md files within the sandbox using list_dir tool."""
    files = []
    try:
        items = list_dir(path)
    except Exception as e:
        print(f"Error listing directory {path}: {e}")
        return []

    for item in items:
        # Construct the relative path for the next call
        item_path = os.path.join(path, item["name"]) if path != "." else item["name"]

        if item["type"] == "dir":
            # Skip common non-content directories
            if item["name"] in [".git", "__pycache__", ".venv", "indices", "artifacts"]:
                continue
            files.extend(await find_md_files(item_path))
        elif item["type"] == "file" and item["name"].lower().endswith(".md"):
            files.append(item_path)
    return files


def extract_first_heading(content: str) -> str:
    """Extract the first # Heading from markdown content."""
    match = re.search(r"^#\s+(.*)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


async def main():
    print("--- Markdown Embedding Pipeline ---")

    # 1. Discover MD files in the sandbox
    print("Searching for markdown files...")
    md_files = await find_md_files(".")
    print(f"Found {len(md_files)} markdown files.")

    # 2. Extract content and metadata
    data_to_embed = []
    for file_path in md_files:
        try:
            # read_file expects a path relative to the sandbox
            file_info = read_file(file_path)
            content = file_info["content"]
            file_name = os.path.basename(file_path)
            first_heading = extract_first_heading(content)

            data_to_embed.append(
                {
                    "file_name": file_name,
                    "file_path": file_path,
                    "first_heading": first_heading,
                    "content": content,
                }
            )
            print(f"  Processed: {file_path}")
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")

    if not data_to_embed:
        print("No content found to embed. Exiting.")
        return

    # 3. Create FAISS index via the tool
    index_name = "markdown_files"
    print(f"\nCreating FAISS index '{index_name}' with {len(data_to_embed)} files...")

    try:
        result = await create_faiss_index(index_name=index_name, data=data_to_embed)

        if result.get("ok"):
            print("\nPipeline Completed Successfully!")
            print(f"Index Path:   {result['index_path']}")
            print(f"Metadata Path: {result['meta_path']}")
            print(f"Dimension:    {result['dimension']}")
            print(f"Total Items:  {result['count']}")
        else:
            print(f"\nFailed to create index: {result.get('error')}")
            if "hint" in result:
                print(f"Hint: {result['hint']}")
    except Exception as e:
        print(f"\nAn error occurred during indexing: {e}")


if __name__ == "__main__":
    asyncio.run(main())
