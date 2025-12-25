import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# 1. 鎖定並強制載入 .env
current_dir = Path(__file__).parent
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path, override=True)

def generate_project_plan(course_name, members, assignment_text, current_date, due_date):
    """
    根據課程資訊與作業說明，呼叫學校 LLM API 生成專案規劃。
    """
    
    # 1. 取得並清理 API Key
    raw_key = os.getenv("API_KEY")
    if not raw_key:
        return "❌ 錯誤：找不到 API_KEY，請檢查 .env 檔案。"
    
    api_key = raw_key.strip() # 去除空白
    api_url = os.getenv("API_URL")
    model_name = os.getenv("MODEL_NAME", "gpt-oss:120b")

    # 2. 準備 Prompt (提示詞) - 這是關鍵修改處
    prompt = f"""
    你是一個專業的專案經理與學術顧問。請根據以下資訊，為學生團隊生成一份詳細的期末專案規劃。

    【課程名稱】：{course_name}
    【組員名單】：{members}
    【作業說明】：{assignment_text}
    【時間限制】：今天是 {current_date}，專案死線是 {due_date}。請根據這段時間長度，規劃合理的進度檢查點。

    ---
    【格式嚴格要求】：
    1. **請輸出純文字 (Plain Text)**，以便直接貼入 Google Docs。
    2. **禁止**使用 Markdown 表格語法（不要出現 | 符號）。
    3. **禁止**使用 Markdown 粗體語法（不要出現 ** 星號）。
    4. **禁止**使用 Markdown 標題語法（不要出現 ## 井號）。
    5. 標題請改用【中括號】表示，例如：【一、專案目標】。
    6. 時程規劃請改用【里程碑倒推法】，例如：「12/20 前完成：[任務名稱] (負責人)」。

    ---
    請生成一份包含以下章節的專案規劃書：
    1. 專案題目發想 (給出 3 個與課程相關的題目建議)
    2. 專案目標
    3. 任務分配 (根據組員人數分配工作)
    4. 關鍵時程與里程碑 (請列出 3-4 個具體的檢查點日期與產出物)
    5. 預期困難與解決方案
    """

    # 3. 設定 API 請求
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

    print(f"🚀 正發送請求至 {api_url} (模型: {model_name})...")

    # 4. 發送請求
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=(10, 120))
        
        if response.status_code != 200:
            return f"❌ API 請求失敗 (Status: {response.status_code}): {response.text}"

        result_json = response.json()
        
        # 解析回應
        content = ""
        if "message" in result_json and "content" in result_json["message"]:
            content = result_json["message"]["content"]
        elif "response" in result_json:
            content = result_json["response"]
        else:
            return f"❌ 回傳格式無法解析：{result_json}"
            
        # --- 雙重保險：手動濾除殘留的 Markdown 符號 ---
        clean_content = content.replace("**", "").replace("##", "").replace("###", "")
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