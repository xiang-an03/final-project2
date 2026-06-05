from flask import Flask, render_template, request, jsonify
import requests
import wikipediaapi
from concurrent.futures import ThreadPoolExecutor
import urllib.parse

app = Flask(__name__)

# 初始化維基百科 API
wiki = wikipediaapi.Wikipedia(
    user_agent="GlobalIdealTypeProject/5.0 (your_email@example.com)",
    language="zh"
)

def get_global_celebrities_by_gender(gender_pref):
    url = "https://query.wikidata.org/sparql"
    wikidata_gender = "wd:Q6581097" if gender_pref == "male" else "wd:Q6581072"
    
    query = f"""
    SELECT DISTINCT ?itemLabel WHERE {{
      ?item wdt:P106 ?occupation .
      VALUES ?occupation {{ wd:Q33999 wd:Q177220 wd:Q1048744 }} .
      ?item wdt:P21 {wikidata_gender} .
      ?article schema:about ?item ;
               schema:isPartOf <https://zh.wikipedia.org/> .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh-tw,zh-hk,zh-cn,zh". }}
    }}
    LIMIT 250 
    """
    try:
        response = requests.get(url, params={'format': 'json', 'query': query}, timeout=10)
        data = response.json()
        return [row['itemLabel']['value'] for row in data['results']['bindings'] 
                if not row['itemLabel']['value'].startswith("Q")]
    except:
        # 備用名人資料庫
        if gender_pref == 'male':
            return ["田柾國", "許光漢", " 王鶴棣", "車銀優", "邊佑錫", "彭于晏", "金泰亨", "玄彬", "GD"]
        else:
            return ["IU", "迪麗熱巴", "Karina", "Winter", "王淨", "子瑜", "三上悠亞", "葉舒華", "張員瑛"] 
# 標準平實特徵關鍵字資料庫（已移除恐龍系）
FEATURE_KEYWORDS = {
    "dog_style": ["犬系", "狗狗眼", "陽光", "親切", "無辜", "暖男"],
    "cat_style": ["貓系", "鳳眼", "神祕", "精緻", "厭世"],
    "fox_style": ["狐狸系", "狐狸眼", "魅惑", "勾人"],
    "single_eyelid": ["單眼皮", "內雙"],
    "double_eyelid": ["雙眼皮", "大眼睛", "桃花眼"],
    "has_tearbags": ["臥蠶", "眼袋"],
    "high_bridge": ["高鼻梁", "挺鼻", "立體"],
    "thick_lips": ["厚唇", "性感嘴唇", "豐滿"],
    "thin_lips": ["薄唇", "櫻桃小嘴"],
    "has_dimple": ["酒窩", "梨渦"],
    "baby_face": ["童顏", "娃娃臉", "圓臉"],
    "v_shape_face": ["V臉", "瓜子臉", "尖下巴"],
    "high_cheekbones": ["高顴骨", "高級臉", "骨相"],
    "humorous": ["幽默", "風趣", "搞笑", "綜藝"],
    "gentle": ["溫柔", "沉穩", "低調", "內斂", "細心"],
    "cool": ["高冷", "酷", "話少"],
    "cute": ["可愛", "呆萌", "撒嬌"],
    "singer": ["歌手", "專輯", "單曲", "演唱會", "樂團"],
    "actor": ["演員", "戲劇", "電影", "主演", "影集"],
    "idol": ["偶像", "練習生", "男團", "女團", "K-pop"],
    "tall": ["高挑", "長腿", "高個子"],
    "petite": ["嬌小", "可愛", "160公分"],
    "fit": ["精壯", "肌肉", "健身", "線條", "腹肌"],
    "compose": ["創作", "作詞", "作曲"]
}

def process_single_artist(artist, selected_features):
    try:
        page = wiki.page(artist)
        if not page.exists(): return None
        full_text = page.text
        score = sum(1 for f in selected_features if any(k in full_text for k in FEATURE_KEYWORDS.get(f, [])))
        if score > 0:
            encoded_name = urllib.parse.quote(artist)
            instagram_url = f"https://www.instagram.com/explore/tags/{encoded_name}/"
            photo_url = f"https://www.google.com/search?tbm=isch&q={encoded_name}"
            
            return {
                "name": artist,
                "score": score,
                "summary": page.summary[:120] + "...",
                "wikipedia_url": page.fullurl,
                "instagram_url": instagram_url,
                "photo_url": photo_url
            }
    except:
        pass
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/match', methods=['POST'])
def match_ideal_type():
    user_data = request.json
    gender_pref = user_data.get('q1')
    selected_features = user_data.get('features', [])
    
    celebrity_pool = get_global_celebrities_by_gender(gender_pref)
    
    results = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(process_single_artist, artist, selected_features) for artist in celebrity_pool]
        for future in futures:
            res = future.result()
            if res: results.append(res)
                
    if not results:
        return jsonify({"message": "沒有找到完全符合的對象，試著多選一些特徵吧！"}), 404
        
    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results[0])

handler = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)