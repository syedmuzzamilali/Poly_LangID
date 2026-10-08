import sys
import re

file_path = r'c:\Users\takweer\3D Objects\prmtblids\webapp\templates\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add a <dialog> modal to the end of the <body>
modal_html = """
    <!-- Dataset Details Modal -->
    <dialog id="dataset-modal" style="border: none; border-radius: 12px; padding: 24px; max-width: 500px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); backdrop-filter: blur(10px);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 id="modal-title" style="margin: 0; color: #1a1a1a;">Dataset Details</h3>
            <button onclick="document.getElementById('dataset-modal').close()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: #666;">&times;</button>
        </div>
        <p id="modal-desc" style="color: #4a4a4a; line-height: 1.5;"></p>
        <div style="margin-top: 20px; text-align: right;">
            <button onclick="document.getElementById('dataset-modal').close()" style="background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">Close</button>
        </div>
    </dialog>
    
    <script>
        const datasetInfo = {
            'Japanese-English': 'Sourced via synthetic generation, combining clean monolingual sentences from Wikipedia and Tatoeba into cross-script code-switched examples.',
            'Russian-English': 'Sourced via synthetic generation, combining clean monolingual sentences from Wikipedia and Tatoeba into cross-script code-switched examples.',
            'Greek-English': 'Sourced via synthetic generation, combining clean monolingual sentences from Wikipedia and Tatoeba into cross-script code-switched examples.',
            'ASCEND Chinese-English': 'Sourced from the ASCEND (A Spontaneous Chinese-English Dataset) corpus, containing transcripts of conversational speech and text.',
            'CSTD Arabic-English': 'Sourced from the CSTD (Code-Switching Twitter Dataset) covering Arabic and English multilingual social media posts.',
            'Indonesian-English': 'Sourced from the "825_Indonesian_English_CodeMixed" dataset, consisting of raw, uncleaned Twitter posts containing heavy social media noise.',
            'TongueSwitcher German-English': 'Sourced from the TongueSwitcher corpus, containing natural code-switching primarily found on Reddit and Twitter.',
            'Turkish-German': 'Sourced from bilingual social media data (Twitter), capturing informal Turkish-German code-switching patterns.'
        };

        function showDatasetDetails(name) {
            document.getElementById('modal-title').innerText = name;
            document.getElementById('modal-desc').innerText = datasetInfo[name] || 'Information not available.';
            document.getElementById('dataset-modal').showModal();
        }
    </script>
</body>
"""

if 'id="dataset-modal"' not in html:
    html = html.replace('</body>', modal_html)

# Add clickable styling to the table rows and onclick handlers
def make_row_clickable(match):
    dataset_name_html = match.group(1)
    # Extract the inner text without HTML tags for the JS function
    clean_name = re.sub(r'<[^>]+>', '', dataset_name_html).strip()
    return f'<tr onclick="showDatasetDetails(\'{clean_name}\')" style="cursor: pointer; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor=\'#f5f7fa\'" onmouseout="this.style.backgroundColor=\'\'"><td>{dataset_name_html}</td>'

# Find all <tr><td><strong>Dataset Name</strong></td>
html = re.sub(r'<tr><td>(<strong>[^<]+</strong>)</td>', make_row_clickable, html)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Added modal successfully")
