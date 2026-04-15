import os
import argparse
import sys

def rename_originals(project_path):
    originals_dir = os.path.join(project_path, "originales")
    if not os.path.exists(originals_dir):
        print(f"Error: Directory {originals_dir} not found.")
        return

    # Get project name from path
    project_name = os.path.basename(project_path.rstrip(os.sep))
    
    # Supported extensions
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    
    # List files and sort by creation time to maintain sequence
    files = [f for f in os.listdir(originals_dir) if f.lower().endswith(valid_extensions)]
    files.sort(key=lambda x: os.path.getctime(os.path.join(originals_dir, x)))

    print(f"Found {len(files)} files to rename in {originals_dir}")

    for i, filename in enumerate(files, 1):
        ext = os.path.splitext(filename)[1]
        new_name = f"{project_name}_v{i:02d}{ext}"
        
        old_file = os.path.join(originals_dir, filename)
        new_file = os.path.join(originals_dir, new_name)
        
        # Avoid renaming if it's already named correctly
        if filename == new_name:
            continue
            
        try:
            os.rename(old_file, new_file)
            print(f"Renamed: {filename} -> {new_name}")
        except Exception as e:
            print(f"Error renaming {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename original images sequentially for the Fotos Premium workflow.")
    parser.add_argument("--project_dir", required=True, help="Path to the project directory containing internal 'originales' folder.")
    
    args = parser.parse_args()
    rename_originals(args.project_dir)
