import json
import csv
import os
import glob

def generate_anki_csv(json_dir, output_csv_path):
    pos_map = {
        "명사": "名詞", "대명사": "代名詞", "수사": "数詞",
        "조사": "助詞", "동사": "動詞", "형용사": "形容詞",
        "관형사": "連体詞", "부사": "副詞", "감탄사": "感動詞",
        "접사": "接辞", "의존 명사": "依存名詞", "보조 동사": "補助動詞",
        "보조 형용사": "補助形容詞", "어미": "語尾",
        "관용구": "慣用句", "속담": "ことわざ"
    }

    merged_items = {}

    json_files = glob.glob(os.path.join(json_dir, '*.json'))
    
    for json_path in json_files:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        items = data.get('channel', {}).get('item', [])
        
        for item in items:
            word_info = item.get('wordInfo', {})
            sense_info = item.get('senseInfo', {})
            
            word = word_info.get('org_word', word_info.get('word', ''))
            if not word: continue
                
            sup_no = word_info.get('sup_no', '')
            if sup_no == '0': sup_no = ''
            
            word_no = word_info.get('word_no', '')

            grade = word_info.get('im_cnt', '')
            key = (word, sup_no)
            sense_list = sense_info.get('senseDataList', [])
            
            if key not in merged_items:
                merged_items[key] = {
                    'word': word,
                    'sup_no': sup_no,
                    'word_no': word_no,
                    'sp_code_name': word_info.get('sp_code_name', ''),
                    'pronun_list': word_info.get('pronunList', []),
                    'senses': sense_list.copy(),
                    'tags': {grade} if grade else set()
                }
            else:
                existing_senses = merged_items[key]['senses']
                existing_defs = {s.get('definition', '').strip() for s in existing_senses}
                for new_sense in sense_list:
                    new_def = new_sense.get('definition', '').strip()
                    if new_def and new_def not in existing_defs:
                        existing_senses.append(new_sense)
                        existing_defs.add(new_def)
                if grade:
                    merged_items[key]['tags'].add(grade)

    with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Ankiのフィールドにマッピングしやすいようにヘッダーを出力
        headers = ['표제어', '동형어 번호', '품사_한국어', '품사_일본어', '발음', '오디오', '의미_목록', "word_no", '테그']
        writer.writerow(headers)
        
        for key, data_val in merged_items.items():
            word = data_val['word']
            sup_no = data_val['sup_no']
            word_no = data_val['word_no']
            sp_code_name = data_val['sp_code_name']
            jp_pos = pos_map.get(sp_code_name, sp_code_name)
            pronun_list = data_val['pronun_list']
            senses = data_val['senses']
            tags_str = " ".join(data_val['tags'])
            
            pronunciation = ""
            sound_url = ""
            if pronun_list:
                pronunciation = pronun_list[0].get('pronunciation', '')
                sound_url = pronun_list[0].get('sound', '')

            # 意味リストのHTML構造化 (レイアウトや余白は一切持たせず、意味構造だけを出力)
            meanings_html = ""
            multi_sense = len(senses) > 1
            
            for idx, sense in enumerate(senses, 1):
                definition = sense.get('definition', '')
                multilan_list = sense.get('multilanList', [])
                multi_translation = ""
                multi_definition = ""
                if multilan_list:
                    multi_translation = multilan_list[0].get('multi_translation', '')
                    multi_definition = multilan_list[0].get('multi_definition', '')
                
                sense_num = f'<span class="sense-num">{idx}. </span>' if multi_sense else ''
                
                sense_html = '<div class="sense-item">'
                if multi_translation:
                    sense_html += f'<div class="sense-trans">{sense_num}{multi_translation}</div>'
                if definition:
                    sense_html += f'<div class="sense-def-kr">{definition}</div>'
                if multi_definition:
                    sense_html += f'<div class="sense-def-jp">{multi_definition}</div>'
                sense_html += '</div>'
                
                meanings_html += sense_html
            
            meanings_html = meanings_html.replace('\n', '')
            
            writer.writerow([word, sup_no, sp_code_name, jp_pos, pronunciation, sound_url, meanings_html, word_no, tags_str])

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(script_dir, 'input_json')
    output_csv = os.path.join(script_dir, './output_csv/korean_anki_data.csv')
    generate_anki_csv(json_dir, output_csv)