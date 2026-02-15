import os

print("🔧 Fixing batches API with proper encoding...")

# Path to server.py
file_path = os.path.join('app', 'server.py')

try:
    # Read file with utf-8 encoding
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("✅ File read successfully!")
    
    # Look for the batches route
    if "@app.route('/api/batches', methods=['GET'])" in content:
        print("✅ Found batches route, preparing fix...")
        
        # Simple fix - just add a print statement to debug
        new_content = content.replace(
            "def get_all_batches():",
            """def get_all_batches():
    print("📊 Batches API called")"""
        )
        
        # Write back with utf-8 encoding
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Fixed! Added debug print")
    else:
        print("❌ Could not find batches route")
        
except FileNotFoundError:
    print(f"❌ File not found: {file_path}")
    print("Let's search for server.py...")
    
    # Search for server.py
    for root, dirs, files in os.walk("."):
        for file in files:
            if file == "server.py":
                print(f"✅ Found at: {os.path.join(root, file)}")
                file_path = os.path.join(root, file)
                
                # Try again with found path
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add debug print
                new_content = content.replace(
                    "def get_all_batches():",
                    """def get_all_batches():
    print("📊 Batches API called")"""
                )
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✅ Fixed at new location!")
                break
except UnicodeDecodeError as e:
    print(f"❌ Encoding error: {e}")
    print("Trying different encoding...")
    
    # Try with different encoding
    encodings = ['latin-1', 'cp1252', 'iso-8859-1']
    
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            print(f"✅ Success with {enc} encoding")
            
            # Simple fix - just add a print
            new_content = content.replace(
                "def get_all_batches():",
                """def get_all_batches():
    print("📊 Batches API called")"""
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Fixed!")
            break
        except:
            print(f"❌ Failed with {enc}")
            continue