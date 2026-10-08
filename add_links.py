import sys

file_path = r'c:\Users\takweer\3D Objects\prmtblids\webapp\templates\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

old_script_start = "const datasetInfo = {"
old_script_end = "function showDatasetDetails(name)"

start_idx = html.find(old_script_start)
end_idx = html.find(old_script_end)

if start_idx == -1 or end_idx == -1:
    print('Could not find script block!')
    sys.exit(1)

new_dict_code = """const datasetInfo = {
            'Japanese-English': 'Sourced via synthetic generation, combining clean monolingual sentences into cross-script code-switched examples. <br><br><b>Source:</b> Local Generation (Wikipedia/Tatoeba)',
            'Russian-English': 'Sourced via synthetic generation, combining clean monolingual sentences into cross-script code-switched examples. <br><br><b>Source:</b> Local Generation (Wikipedia/Tatoeba)',
            'Greek-English': 'Sourced via synthetic generation, combining clean monolingual sentences into cross-script code-switched examples. <br><br><b>Source:</b> Local Generation (Wikipedia/Tatoeba)',
            'ASCEND Chinese-English': 'Sourced from the ASCEND (A Spontaneous Chinese-English Dataset) corpus, containing transcripts of conversational speech and text. <br><br><b>Source:</b> <a href="https://huggingface.co/datasets/CAiRE/ASCEND" target="_blank" style="color: #007bff; text-decoration: none;">HuggingFace: CAiRE/ASCEND</a>',
            'CSTD Arabic-English': 'Sourced from the CSTD (Code-Switching Twitter Dataset) covering Arabic and English multilingual social media posts. <br><br><b>Source:</b> <a href="https://github.com/Maha-Althobaiti/CSTD" target="_blank" style="color: #007bff; text-decoration: none;">GitHub: Maha-Althobaiti/CSTD</a>',
            'Indonesian-English': 'Sourced from the "825_Indonesian_English_CodeMixed" dataset, consisting of raw, uncleaned Twitter posts containing heavy social media noise. <br><br><b>Source:</b> <a href="https://github.com/zainhas/825_Indonesian_English_CodeMixed" target="_blank" style="color: #007bff; text-decoration: none;">GitHub: zainhas/825_Indonesian_English_CodeMixed</a>',
            'TongueSwitcher German-English': 'Sourced from the TongueSwitcher corpus, containing natural code-switching primarily found on Reddit and Twitter. <br><br><b>Source:</b> <a href="https://github.com/mshenoda/tongueswitcher" target="_blank" style="color: #007bff; text-decoration: none;">GitHub: mshenoda/tongueswitcher</a>',
            'Turkish-German': 'Sourced from bilingual social media data (Twitter), capturing informal Turkish-German code-switching patterns. <br><br><b>Source:</b> <a href="https://huggingface.co/datasets/boun-tabi-LMG/turkish-german-code-switching" target="_blank" style="color: #007bff; text-decoration: none;">HuggingFace: turkish-german-code-switching</a>'
        };

        """

html = html[:start_idx] + new_dict_code + html[end_idx:]

# Also, let's update the modal description paragraph to allow HTML injection by using innerHTML instead of innerText
html = html.replace("document.getElementById('modal-desc').innerText = datasetInfo[name]", "document.getElementById('modal-desc').innerHTML = datasetInfo[name]")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated links successfully")
