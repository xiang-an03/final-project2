from flask import Flask, render_template, request, jsonify
import requests
import wikipediaapi
from concurrent.futures import ThreadPoolExecutor

# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 Wikipedia API
wiki = wikipediaapi.Wikipedia(
    user_agent="GlobalIdealTypeProject/5.0 (your_email@example.com)",
    language="zh"
)

# 根據性別從 Wikidata 動態抓取全球明星
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
    LIMIT 200 
    """
    try:
        response = requests.get(url, params={'format': 'json', 'query': query}, timeout=10)
        data = response.json()
        return [row['itemLabel']['value'] for row in data['results']['bindings'] 
                if not row['itemLabel']['value'].startswith("Q")]
    except:
        if gender_pref == 'male':
            return ["周杰倫", "許光漢", "林俊傑", "車銀優", "邊佑錫", "彭于晏"]
        else:
            return ["IU", "Taylor Swift", "Karina", "蔡依林", "王淨", "子瑜"]

# 特徵關鍵字字典
FEATURE_KEYWORDS = {
    "dog_style": ["犬系", "狗狗眼", "陽光", "親切", "無辜", "暖男"],
    "cat_style": ["貓系", "鳳眼", "高冷", "傲嬌", "神祕", "精緻", "厭世"],
    "has_dimple": ["酒窩", "梨渦"],
    "single_eyelid": ["單眼皮", "內雙"],
    "high_bridge": ["高鼻梁", "挺拔", "立體"],
    "baby_face": ["童顏", "娃娃臉", "凍齡"],
    "humorous": ["幽默", "風趣", "搞笑", "綜藝感"],
    "gentle": ["溫柔", "沉穩", "低調", "內斂", "細心"],
    "cool": ["高冷", "酷帥", "不愛說話"],
    "singer": ["歌手", "專輯", "單曲", "演唱會"],
    "actor": ["演員", "戲劇", "電影", "主演"],
    "idol": ["偶像", "練習生", "男團", "女團", "K-pop"],
    "rapper": ["饒舌", "Rap", "說唱"],
    "tall": ["高挑", "長腿", "180cm", "185cm"],
    "petite": ["嬌小", "可愛", "160cm"],
    "fit": ["精壯", "肌肉", "健身", "線條"],
    "compose": ["創作", "作詞", "作曲"],
    "dance": ["舞蹈", "跳舞", "主舞"],
    "instrument": ["鋼琴", "吉他", "樂器"],
    "sports": ["運動", "健身", "籃球"],
    "mbti_e": ["活潑", "外向", "熱情", "E人"],
    "mbti_i": ["安靜", "內向", "宅", "I人"]
}

def process_single_artist(artist, selected_features):
    try:
        page = wiki.page(artist)
        if not page.exists(): return None
        full_text = page.text
        score = sum(1 for f in selected_features if any(k in full_text for k in FEATURE_KEYWORDS.get(f, [])))
        if score > 0:
            return {
                "name": artist,
                "score": score,
                "summary": page.summary[:100] + "...",
                "url": page.fullurl
            }
    except:
        pass
    return None

# 首頁路由
@app.route('/')
def home():
    return render_template('index.html')

# 匹配 API 路由
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
                
    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results[:5])

# 指派給 Vercel 的 handler 接口
handler = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)