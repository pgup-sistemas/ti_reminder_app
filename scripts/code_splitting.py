import os
import re
from pathlib import Path

# Configuration
JS_SOURCE_DIR = os.path.join('app', 'static', 'js')
JS_OUTPUT_DIR = os.path.join('app', 'static', 'js', 'chunks')
ENTRY_POINTS = {
    'dashboard': ['dashboard.js'],
    'tarefas': ['tarefas.js'],
    'chamados': ['chamados.js'],
    'equipamentos': ['equipamentos.js'],
    'tutoriais': ['tutoriais.js']
}

def ensure_dir(directory):
    """Ensure the output directory exists."""
    os.makedirs(directory, exist_ok=True)

def extract_imports(js_content):
    """Extract import statements from JavaScript content."""
    # Match both ES6 import and require() syntax
    import_pattern = re.compile(
        r'(?:import\s*(?:{[^}]*}\s*from\s*)?["\']([^"\']+)["\']|'  # ES6 imports
        r'require\(\s*["\']([^"\']+)["\']\s*\))'  # CommonJS requires
    )
    return [m[0] or m[1] for m in import_pattern.findall(js_content)]

def create_chunk(entry_point, output_dir):
    """Create a chunk file for the given entry point."""
    input_path = os.path.join(JS_SOURCE_DIR, entry_point)
    if not os.path.exists(input_path):
        print(f"⚠️  Entry point not found: {entry_point}")
        return
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract imports and create a dependency graph
    imports = extract_imports(content)
    
    # For now, we'll just copy the file to the chunks directory
    # In a real implementation, you would use a bundler like webpack or rollup
    output_path = os.path.join(output_dir, f"chunk-{entry_point}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"// Chunk for {entry_point}\n")
        f.write(f"// Dependencies: {', '.join(imports)}\n\n")
        f.write(content)
    
    return output_path

def generate_loader_script(chunks, output_dir):
    """Generate a loader script to dynamically load chunks."""
    loader_content = """// Auto-generated chunk loader
class ChunkLoader {
    constructor() {
        this.loadedChunks = new Set();
        this.chunks = %s;
    }

    async loadChunk(chunkName) {
        if (this.loadedChunks.has(chunkName)) {
            console.log(`Chunk ${chunkName} already loaded`);
            return Promise.resolve();
        }

        const chunkPath = this.chunks[chunkName];
        if (!chunkPath) {
            console.error(`Chunk ${chunkName} not found`);
            return Promise.reject(new Error(`Chunk ${chunkName} not found`));
        }

        console.log(`Loading chunk: ${chunkName}`);
        
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = chunkPath;
            script.onload = () => {
                this.loadedChunks.add(chunkName);
                console.log(`Chunk ${chunkName} loaded successfully`);
                resolve();
            };
            script.onerror = (error) => {
                console.error(`Failed to load chunk ${chunkName}:`, error);
                reject(error);
            };
            document.head.appendChild(script);
        });
    }

    // Preload chunks without executing them
    preloadChunks(chunkNames) {
        return Promise.all(
            chunkNames.map(chunkName => {
                if (this.loadedChunks.has(chunkName)) {
                    return Promise.resolve();
                }
                
                const chunkPath = this.chunks[chunkName];
                if (!chunkPath) {
                    console.warn(`Chunk ${chunkName} not found for preloading`);
                    return Promise.resolve();
                }

                return new Promise((resolve) => {
                    const link = document.createElement('link');
                    link.rel = 'preload';
                    link.as = 'script';
                    link.href = chunkPath;
                    link.onload = resolve;
                    link.onerror = resolve; // Don't fail the whole preload if one fails
                    document.head.appendChild(link);
                });
            })
        );
    }
}

// Create a global instance
window.chunkLoader = new ChunkLoader();
"""
    
    # Convert chunks to a format suitable for the loader
    chunk_map = {name: f"/static/js/chunks/chunk-{name}" for name in chunks}
    loader_content = loader_content % str(chunk_map)
    
    loader_path = os.path.join(output_dir, 'chunk-loader.js')
    with open(loader_path, 'w', encoding='utf-8') as f:
        f.write(loader_content)
    
    return loader_path

def update_html_templates():
    """Update HTML templates to use the new chunk loading system."""
    templates_dir = os.path.join('app', 'templates')
    
    for template_file in os.listdir(templates_dir):
        if not template_file.endswith('.html'):
            continue
            
        template_path = os.path.join(templates_dir, template_file)
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already updated
        if 'chunk-loader.js' in content:
            continue
            
        # Add chunk loader before the closing </body> tag
        if '</body>' in content:
            loader_script = (
                '\n    <!-- Chunk loader -->\n    <script src="{{ url_for(\'static\', filename=\'js/chunks/chunk-loader.js\') }}"></script>\n    <script>\n        // Example: Load chunks based on the current page\n        document.addEventListener(\'DOMContentLoaded\', () => {\n            const pageChunks = []; // Add chunks needed for this page\n            if (pageChunks.length > 0) {\n                window.chunkLoader.preloadChunks(pageChunks);\n            }\n        });\n    </script>\n    \n</body>'
            )
            
            updated_content = content.replace('</body>', loader_script)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ Updated: {template_file}")

def main():
    print("🚀 Starting code splitting...")
    
    # Ensure output directory exists
    ensure_dir(JS_OUTPUT_DIR)
    
    # Process entry points
    chunks = {}
    for chunk_name, entry_points in ENTRY_POINTS.items():
        for entry_point in entry_points:
            chunk_path = create_chunk(entry_point, JS_OUTPUT_DIR)
            if chunk_path:
                chunks[chunk_name] = chunk_path
    
    # Generate loader script
    if chunks:
        loader_path = generate_loader_script(chunks.keys(), JS_OUTPUT_DIR)
        print(f"\n✨ Generated {len(chunks)} chunks and loader script")
        print(f"   - Loader: {loader_path}")
        
        # Update HTML templates
        print("\n🔄 Updating HTML templates...")
        update_html_templates()
        
        print("\n✅ Code splitting complete!")
        print("💡 Next steps:")
        print("   1. Move your page-specific JavaScript to separate modules")
        print("   2. Update the ENTRY_POINTS dictionary with your actual entry points")
        print("   3. Use chunkLoader.loadChunk('chunkName') to load chunks on demand")
    else:
        print("⚠️  No chunks were generated. Check your entry points configuration.")

if __name__ == "__main__":
    main()
