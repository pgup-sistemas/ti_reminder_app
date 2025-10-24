import os
import shutil

# Limpar cache Python
for root, dirs, files in os.walk('app'):
    if '__pycache__' in dirs:
        cache_path = os.path.join(root, '__pycache__')
        print(f"Removendo: {cache_path}")
        shutil.rmtree(cache_path)
    for file in files:
        if file.endswith('.pyc'):
            pyc_path = os.path.join(root, file)
            print(f"Removendo: {pyc_path}")
            os.remove(pyc_path)

print("✅ Cache limpo!")
