import streamlit as st
import time
import datetime
import graphviz
# 確保這些檔案都在同一個目錄下
from google_utils import get_google_service, create_doc_with_content, share_file_permissions, send_gmail
from llm_helper import extract_text_from_pdf, generate_project_plan

# --- 頁面設定 ---
st.set_page_config(page_title="Course Agent", page_icon="🤖", layout="wide")

# --- 狀態圖繪製 (符合 Report 要求) ---
def draw_dag():
    graph = graphviz.Digraph()
    graph.attr(rankdir='LR')
    # 定義節點
    graph.node('A', 'Start: User Input', shape='oval')
    graph.node('B', 'LLM: Analyze PDF & Plan', shape='box', style='filled', fillcolor='lightblue')
    graph.node('C', 'Tool: Create Google Doc', shape='box', style='filled', fillcolor='lightyellow')
    graph.node('D', 'Tool: Set Permissions', shape='box', style='filled', fillcolor='lightyellow')
    graph.node('E', 'Tool: Send Email Invite', shape='box', style='filled', fillcolor='lightyellow')
    graph.node('F', 'End: Success', shape='oval', style='filled', fillcolor='lightgreen')

    # 定義連線
    graph.edge('A', 'B')
    graph.edge('B', 'C')
    graph.edge('C', 'D')
    graph.edge('D', 'E')
    graph.edge('E', 'F')
    return graph

# --- 主程式 ---
def main():
    st.title("🎓 自動化期末報告組隊 Agent")
    st.markdown("### Intelligent Agent for Group Projects")
    
    # 左側邊欄：系統狀態與 Google 登入
    with st.sidebar:
        st.header("⚙️ 系統設定")
        st.info("請先登入 Google 帳號以啟用 Agent 工具")
        
        # 初始化 session_state
        if 'services' not in st.session_state:
            st.session_state.services = None

        if st.button("🔑 登入 Google"):
            try:
                # 這裡會觸發 OAuth 登入流程
                gmail, drive, docs = get_google_service()
                if gmail:
                    st.session_state.services = (gmail, drive, docs)
                    st.success("登入成功！")
            except Exception as e:
                st.error(f"登入失敗: {e}")
        
        # 顯示目前登入狀態
        if st.session_state.services:
            st.success("✅ Google 服務已連線")
        
        # 顯示 DAG 圖
        st.divider()
        st.markdown("**System Logic (DAG)**")
        st.graphviz_chart(draw_dag())

    # 主畫面區塊
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1️⃣ 輸入專案資訊")
        with st.form("project_input"):
            course_name = st.text_input("課程名稱", "計算理論")
            # 這裡輸入 raw_ids (字串)，方便直接傳給 LLM
            raw_ids = st.text_area("組員學號或 Email (用逗號分隔)", "f74122030, joshuatseng0233@gmail.com")
            uploaded_file = st.file_uploader("上傳作業說明 (PDF)", type="pdf")
            default_deadline = datetime.date.today() + datetime.timedelta(days=14)
            deadline = st.date_input("📅 報告截止日期", default_deadline)
            
            submitted = st.form_submit_button("🚀 啟動 Agent")

    with col2:
        st.subheader("2️⃣ Agent 執行日誌")
        log_container = st.container(height=400)

    # --- 執行邏輯 ---
    if submitted:
        # 檢查 1: 是否已登入
        if not st.session_state.services:
            st.error("請先在左側欄登入 Google！")
            st.stop()
            
        # 檢查 2: 是否上傳檔案
        if not uploaded_file:
            st.error("請上傳 PDF 作業說明檔！")
            st.stop()

        # 取得服務物件
        gmail_svc, drive_svc, docs_svc = st.session_state.services
        
        # 處理 Email：將學號轉為學校信箱，如果是完整 Email 則保留
        student_ids_list = [s.strip() for s in raw_ids.split(',')]
        emails = [f"{sid}@gs.ncku.edu.tw" if "@" not in sid else sid for sid in student_ids_list]

        # --- 步驟 1: 讀取 PDF ---
        with log_container:
            st.write("📂 讀取 PDF 中...")
            pdf_text = extract_text_from_pdf(uploaded_file)
            if not pdf_text:
                st.error("❌ 無法讀取 PDF 內容")
                st.stop()
            st.success(f"✅ PDF 讀取完成 ({len(pdf_text)} 字)")

        # --- 步驟 2: LLM 規劃 (關鍵修改處) ---
        with log_container:
            st.write("🤖 LLM 正在分析需求並生成分工表...")
            with st.spinner("思考中 (約需 30-60 秒)..."):
                # 取得今天日期
                today_str = str(datetime.date.today())
                deadline_str = str(deadline)
                
                # 傳入 5 個參數：課程, 組員, PDF內容, 今天日期, 死線
                plan_content = generate_project_plan(course_name, raw_ids, pdf_text, today_str, deadline_str)
            
            # 檢查 LLM 是否回傳錯誤
            if plan_content.startswith("❌"):
                st.error(plan_content)
                st.stop()
                
            st.success("✅ 專案規劃生成完畢！")
            with st.expander("查看生成內容"):
                st.markdown(plan_content)

        # --- 步驟 3: 建立文件 ---
        with log_container:
            st.write("📝 正在建立 Google Doc...")
            doc_title = f"[{course_name}] 期末報告共筆 - Agent生成"
            try:
                doc_id, doc_url = create_doc_with_content(docs_svc, drive_svc, doc_title, plan_content)
                if doc_url:
                    st.success(f"✅ 文件建立成功: [點擊開啟]({doc_url})")
                else:
                    st.error("❌ 文件建立失敗")
                    st.stop()
            except Exception as e:
                st.error(f"建立文件時發生錯誤: {e}")
                st.stop()

        # --- 步驟 4: 設定權限 ---
        with log_container:
            st.write("👥 設定組員權限...")
            try:
                share_file_permissions(drive_svc, doc_id, emails)
                st.success(f"✅ 已將權限分享給: {', '.join(emails)}")
            except Exception as e:
                st.warning(f"⚠️ 權限設定部分失敗 (可能是 Email 格式錯誤): {e}")

        # --- 步驟 5: 寄信 ---
        with log_container:
            st.write("📧 正在寄信通知組員...")
            subject = f"[{course_name}] 期末報告分工通知 (AI Agent)"
            email_body = f"""
            各位同學好：
            
            這是一封由 AI Agent 自動發送的通知。
            針對 {course_name} 的期末報告，我已經根據作業 PDF 產生了初步分工表。
            
            請大家到以下連結開始協作：
            {doc_url}
            
            (此信件為系統自動發送)
            """
            try:
                send_gmail(gmail_svc, emails, subject, email_body)
                st.success("✅ Email 發送完畢！")
            except Exception as e:
                 st.warning(f"⚠️ 寄信失敗: {e}")
            
        st.balloons()
        st.success("🏆 所有流程執行完畢！")

if __name__ == "__main__":
    main()