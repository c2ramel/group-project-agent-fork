import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# 1. 鎖定並強制載入 .env
current_dir = Path(__file__).parent
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path, override=True)

def generate_project_plan(course_name, members, assignment_text, current_date, due_date, output_format="Docs"):
    """
    根據課程資訊與作業說明，呼叫學校 LLM API 生成專案規劃。
    output_format: "Docs" (純文字) 或 "Slides" (JSON)
    """
    
    raw_key = os.getenv("API_KEY")
    if not raw_key:
        return "❌ 錯誤：找不到 API_KEY，請檢查 .env 檔案。"
    
    api_key = raw_key.strip()
    api_url = os.getenv("API_URL")
    model_name = os.getenv("MODEL_NAME", "gpt-oss:120b") # 如果你有改 .env，這裡預設值沒差

    if output_format == "Slides":
            # --- 簡報專用 Prompt (JSON) ---
            prompt = f"""
            你是一個專案經理。
            【課程】：{course_name}
            【組員】：{members}
            【作業說明】：{assignment_text}
            【時間】：今天是 {current_date}，死線是 {due_date}。
            
            請為這份報告生成一份「Google Slides 簡報大綱」。
            
            【格式嚴格要求】：
            1. 請輸出一個標準的 JSON 陣列 (Array)。
            2. **第一頁（封面）必須包含 "title" (大標題) 和 "subtitle" (副標題)。** 副標題請放入組員名單。
            3. **從第二頁開始**，每個物件包含 "title" 和 "points" (重點內容，條列式字串，需換行用 \\n)。
            4. 不要使用 Markdown 語法，只給我純 JSON 字串。
            5. 至少包含 7 張投影片:封面、專案目標、可行方案一、可行方案二、分工表、時間規劃、引用資料

            【範例格式 (請照著這個結構)】：
            [
                {{"title": "{course_name} 期末報告：[題目]", "subtitle": "組員：{members}\\n日期：{current_date}"}},
                {{"title": "專案目標", "points": "1. 目標一\\n2. 目標二"}},
                {{"title": "任務分配", "points": "• 王小明：前端\\n• 李小華：後端"}}
            ]
            """
    else:
        # --- Docs 專用 Prompt (純文字 + 強制範例) ---
        # 修改重點：直接給它看範例，並規定不准畫線
        prompt = f"""
        你是一個專業的專案經理。請根據以下資訊，生成一份期末專案規劃。

        【課程名稱】：{course_name}
        【組員名單】：{members}
        【作業說明】：{assignment_text}
        【時間】：今天是 {current_date}，死線是 {due_date}。

        ---
        【格式嚴格要求 - 絕對禁止使用表格】：
        1. **請輸出純文字 (Plain Text)**。
        2. **禁止出現 | 符號**，禁止使用 Markdown 表格。
        3. 標題請用【中括號】。
        4. **任務分配請務必使用以下格式**：
           - [任務名稱]：[負責人] (產出物：[交付項目])

        【輸出範例 (請照著這個樣子寫)】：
        【一、專案目標】
        本專案旨在開發一個...

        【二、任務分配】
        - 資料爬蟲開發：王小明 (產出物：Python script)
        - 後端 API 架設：李小華 (產出物：API 文件)

        【三、時程規劃】
        - 12/20 前完成：系統架構確認
        ---

        請生成一份包含：1.專案題目建議 2.專案目標 3.任務分配 4.關鍵時程 5.預期困難。
        """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.7}
    }

    print(f"🚀 正發送請求至 {api_url} (模式: {output_format})...")

    try:
        # 將超時時間設為 300 秒 (5分鐘)
        response = requests.post(api_url, headers=headers, json=payload, timeout=(10, 300))
        
        if response.status_code != 200:
            return f"❌ API 請求失敗 (Status: {response.status_code}): {response.text}"

        result_json = response.json()
        
        content = ""
        if "message" in result_json and "content" in result_json["message"]:
            content = result_json["message"]["content"]
        elif "response" in result_json:
            content = result_json["response"]
        else:
            return f"❌ 回傳格式無法解析：{result_json}"
            
        # --- 暴力清理區 (這裡是關鍵！) ---
        # 1. 去除 Markdown 粗體、標題
        clean_content = content.replace("**", "").replace("##", "").replace("###", "")
        
        # 2. 強制去除表格符號 (將 | 替換成空格，將表格分隔線 |---| 替換成空)
        clean_content = clean_content.replace("|---|", "").replace("|", "  ")
        
        return clean_content

    except requests.exceptions.Timeout:
        return "❌ 請求超時：模型生成太久了，請再試一次。"
    except Exception as e:
        return f"❌ 發生未預期的錯誤: {str(e)}"

# PDF 讀取功能保持不變
def extract_text_from_pdf(pdf_file):
    import pypdf
    try:
        pdf_reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"