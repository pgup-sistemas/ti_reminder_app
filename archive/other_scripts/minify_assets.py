import os
import glob
from pathlib import Path
from rcssmin import cssmin
from rjsmin import jsmin

def get_all_assets():
    """Get all CSS and JS files in the static directory."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
    css_files = glob.glob(os.path.join(static_dir, '**', '*.css'), recursive=True)
    js_files = glob.glob(os.path.join(static_dir, '**', '*.js'), recursive=True)
    return css_files, js_files

def minify_file(file_path):
    """Minify a single CSS or JS file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Minify based on file extension
        if file_path.endswith('.css'):
            minified = cssmin(content)
            output_path = file_path.replace('.css', '.min.css')
        elif file_path.endswith('.js'):
            minified = jsmin(content)
            output_path = file_path.replace('.js', '.min.js')
        else:
            return False
            
        # Write minified content to new file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified)
            
        return True
    except Exception as e:
        print(f"Error minifying {file_path}: {str(e)}")
        return False

def main():
    print("🚀 Starting asset minification...")
    css_files, js_files = get_all_assets()
    all_files = css_files + js_files
    
    print(f"🔍 Found {len(all_files)} files to process")
    print("📦 Minifying files...")
    
    success_count = 0
    for file_path in all_files:
        # Skip already minified files
        if '.min.' in file_path:
            continue
            
        if minify_file(file_path):
            success_count += 1
            print(f"✅ Minified: {os.path.basename(file_path)}")
    
    print(f"\n✨ Minification complete!")
    print(f"   - Successfully minified: {success_count} files")
    print(f"   - Total files processed: {len(all_files)}")
    print("\n💡 Tip: Update your HTML templates to reference the .min.js and .min.css files")

if __name__ == "__main__":
    main()
