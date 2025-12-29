import re
import json

def extract_json(text):
    print(f"📥 Input: {text[:50]}...")
    try:
        # The logic we just added to google_utils.py
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            print(f"✅ Success! Extracted {len(data)} items.")
            return True
        else:
            print("❌ No JSON array found.")
            return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
        return False

# Test Cases
messy_inputs = [
    # Case 1: Standard Markdown
    """Here is the plan:\n```json\n[{"title": "Slide 1"}]\n```""",
    
    # Case 2: No Markdown, just text
    """Sure! Here it is: [{"title": "Slide 1"}, {"title": "Slide 2"}] Hope this helps!""",
    
    # Case 3: Mixed content
    """Analyzing...\n\nFound 3 points.\n[{"title": "A"}]\n\nDone."""
]

print("🧪 Testing Robust JSON Parsing...")
for i, case in enumerate(messy_inputs):
    print(f"\n--- Case {i+1} ---")
    extract_json(case)
