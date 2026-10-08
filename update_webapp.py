import sys

file_path = r'c:\Users\takweer\3D Objects\prmtblids\webapp\templates\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

start_marker = '<h3 style="margin-top: 28px;">Standardized Academic Benchmark Results</h3>'
end_marker = '</div>\n            </div>\n        </section>'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Could not find markers!')
    sys.exit(1)

new_content = '''<h3 style="margin-top: 28px;">1. Clean / Multi-Script Datasets</h3>
                <p class="section-desc" style="margin-bottom: 15px;">Standardized sentences crossing distinct Unicode script blocks (e.g., Cyrillic, Greek, Arabic, Han vs. Latin). Due to lack of social media noise, script-detection boundaries perform exceptionally well.</p>
                <div class="table-responsive" style="margin-bottom: 40px;">
                    <table class="tech-table">
                        <thead>
                            <tr>
                                <th>Benchmark Dataset</th>
                                <th>Language Pair / Topology</th>
                                <th>Sentences (N)</th>
                                <th>Token Accuracy</th>
                                <th>Exact Match (EM)</th>
                                <th>Partial Match (PM)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td><strong>Japanese-English</strong></td><td>ja, en (Kanji/Kana - Latin)</td><td>300</td><td><strong>100.00%</strong></td><td><strong>100.00%</strong></td><td>100.00%</td></tr>
                            <tr><td><strong>Russian-English</strong></td><td>ru, en (Cyrillic - Latin)</td><td>300</td><td><strong>100.00%</strong></td><td><strong>100.00%</strong></td><td>100.00%</td></tr>
                            <tr><td><strong>Greek-English</strong></td><td>el, en (Greek - Latin)</td><td>300</td><td><strong>100.00%</strong></td><td><strong>100.00%</strong></td><td>100.00%</td></tr>
                            <tr><td><strong>ASCEND Chinese-English</strong></td><td>zh, en (Han - Latin)</td><td>1000</td><td><strong>97.90%</strong></td><td><strong>89.20%</strong></td><td>99.35%</td></tr>
                            <tr><td><strong>CSTD Arabic-English</strong></td><td>ar, en (Arabic - Latin)</td><td>1000</td><td><strong>98.42%</strong></td><td><strong>85.00%</strong></td><td>99.80%</td></tr>
                        </tbody>
                    </table>
                </div>

                <h3>2. Noisy / Twitter Datasets (Mono-Script)</h3>
                <p class="section-desc" style="margin-bottom: 15px;">Code-Switching entirely within the Latin alphabet. Token Accuracy remains high (77%-94%), but uncleaned Twitter data (emojis, @usernames, slang) heavily drops Exact Match (EM). However, Partial Match (PM) proves the underlying detection engine remains robust (99%+).</p>
                <div class="table-responsive">
                    <table class="tech-table">
                        <thead>
                            <tr>
                                <th>Benchmark Dataset</th>
                                <th>Language Pair / Topology</th>
                                <th>Sentences (N)</th>
                                <th>Token Accuracy</th>
                                <th>Exact Match (EM)</th>
                                <th>Partial Match (PM)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr><td><strong>Indonesian-English</strong></td><td>id, en (Latin - Latin)</td><td>2279</td><td><strong>94.75%</strong></td><td><strong>40.54%</strong></td><td>99.20%</td></tr>
                            <tr><td><strong>TongueSwitcher German-English</strong></td><td>de, en (Latin - Latin)</td><td>954</td><td><strong>92.51%</strong></td><td><strong>23.90%</strong></td><td>100.00%</td></tr>
                            <tr><td><strong>Turkish-German</strong></td><td>tr, de (Latin - Latin)</td><td>196</td><td><strong>77.01%</strong></td><td><strong>19.39%</strong></td><td>99.50%</td></tr>
                        </tbody>
                    </table>
                '''

html = html[:start_idx] + new_content + html[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print('Updated webapp successfully')
