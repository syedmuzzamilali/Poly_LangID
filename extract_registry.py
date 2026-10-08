import json
with open(r'C:\Users\takweer\.gemini\antigravity-ide\brain\40b56767-284a-42f9-9c5f-b23627352fe5\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('step_index') == 1957:
            with open('registry_temp.txt', 'w', encoding='utf-8') as out:
                out.write(obj.get('content', ''))
            print('Saved to registry_temp.txt')
            break
