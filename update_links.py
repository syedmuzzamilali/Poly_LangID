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
            'CSTD Arabic-English': 'Sourced from the ArE-CSTD (Arabic-English Code-Switching Textual Dataset) by SDAIA. <br><br><b>Source:</b> <a href="https://huggingface.co/datasets/SDAIA/ArE-CSTD" target="_blank" style="color: #007bff; text-decoration: none;">HuggingFace: SDAIA/ArE-CSTD</a>',
            'Indonesian-English': 'Sourced from the "id-en-code-mixed" dataset, consisting of raw, uncleaned Twitter posts containing heavy social media noise. <br><br><b>Source:</b> <a href="https://github.com/ir-nlp-csui/id-en-code-mixed" target="_blank" style="color: #007bff; text-decoration: none;">GitHub: ir-nlp-csui/id-en-code-mixed</a>',
            'TongueSwitcher German-English': 'Sourced from the TongueSwitcher corpus, containing natural code-switching primarily found on Reddit and Twitter. <br><br><b>Source:</b> <a href="https://huggingface.co/igorsterner/german-english-code-switching-identification" target="_blank" style="color: #007bff; text-decoration: none;">HuggingFace: igorsterner/german-english-code-switching-identification</a>',
            'Turkish-German': 'Sourced from the TrDeNormData (Turkish-German Code-Switching Corpus), capturing informal Turkish-German Twitter code-switching patterns. <br><br><b>Source:</b> <a href="https://github.com/ozlemcek/TrDeNormData" target="_blank" style="color: #007bff; text-decoration: none;">GitHub: ozlemcek/TrDeNormData</a>'
        };

        """

html = html[:start_idx] + new_dict_code + html[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated verified links successfully")
