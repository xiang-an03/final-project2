import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from google import genai
from pydantic import BaseModel
import urllib.parse
import json

# 載入 .env 檔案的變數
load_dotenv()

app = Flask(__name__)

# 自動從環境變數讀取，程式碼裡再也沒有敏感密鑰了！
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ...(後面其餘程式碼完全不變)...
# 定義嚴格的資料格式，強迫 Gemini 必須遵守，絕不出錯
class MatchResult(BaseModel):
    name: str
    score: str
    summary: str

# 前端 Value 與中文標籤的對照表
TAG_MAP = {
    "dog_style": "犬系風格長相", "cat_style": "貓系風格長相", "fox_style": "狐狸系風格長相",
    "single_eyelid": "單眼皮/內雙", "double_eyelid": "雙眼皮", "has_tearbags": "有臥蠶",
    "mbti_i": "MBTI 的 I 人 (內向型)", "mbti_e": "MBTI 的 E 人 (外向型)",
    "has_dimple": "有酒窩/梨渦", "baby_face": "圓臉/娃娃臉", "v_shape_face": "尖下巴/V臉", "high_cheekbones": "高顴骨",
    "tall": "身材高挑長腿", "petite": "身材嬌小", "fit": "身材精壯/有肌肉",
    "gentle": "溫柔內斂的個性", "humorous": "幽默風趣的個性", "cool": "高冷話少的個性", "cute": "可愛呆萌的個性",
    "singer": "歌手身分", "actor": "演員身分", "idol": "舞台偶像身分", "compose": "會音樂創作"
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/match', methods=['POST'])
def match_ideal_type():
    user_data = request.json
    gender_pref = "男性 (Male)" if user_data.get('q1') == 'male' else "女性 (Female)"
    raw_features = user_data.get('features', [])
    
    chinese_features = [TAG_MAP.get(f, f) for f in raw_features]
    features_str = "、".join(chinese_features) if chinese_features else "未特別指定"

    # 精簡且明確的 Prompt 範圍
    prompt = f"""
    你是全球娛樂圈的大數據專家。請根據使用者的理想型條件，從【亞洲地區】（包含台灣、韓國、日本、中國大陸、香港）挑選出一位最完美符合的真實知名藝人明星。

    使用者期望條件：
    - 性別偏好：{gender_pref} 的亞洲明星
    - 必須具備特徵：{features_str}

    請挑選出一位最符合以上所有特徵的真實亞洲明星。
    - 在 name 欄位填入該明星姓名。
    - 在 score 欄位評估契合度（例如：95%）。
    - 在 summary 欄位寫一段 100 字左右的客製化推薦語，說明為什麼這位明星完美符合他挑選的特徵。
    """

    try:
        # 使用 response_schema 強制限制回傳格式
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': MatchResult,
            }
        )
        
        # 使用官方推薦方式直接載入解析後的 JSON 字典
        import json
        result_data = json.loads(response.text)
        
        # 自動為明星生成對應的搜尋與社群網站動態連結
        encoded_name = urllib.parse.quote(result_data['name'])
        result_data['instagram_url'] = f"https://www.instagram.com/explore/tags/{encoded_name}/"
        result_data['photo_url'] = f"https://www.google.com/search?tbm=isch&q={encoded_name}"
        result_data['wikipedia_url'] = f"https://zh.wikipedia.org/wiki/{encoded_name}"
        
        return jsonify(result_data)

    except Exception as e:
        print("Gemini API 發生錯誤資訊:", str(e))
        return jsonify({"message": f"密鑰或驗證發生錯誤，請檢查 API Key 是否正確！(錯誤: {str(e)})"}), 500

handler = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)