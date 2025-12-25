import os
import pickle
import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import streamlit as st

# 設定權限範圍
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

def get_google_service():
    """處理 OAuth 2.0 登入與憑證"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                st.error("❌ 找不到 credentials.json，請確認檔案已放入專案目錄！")
                return None, None, None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return (
        build('gmail', 'v1', credentials=creds),
        build('drive', 'v3', credentials=creds),
        build('docs', 'v1', credentials=creds)
    )

def create_doc_with_content(service_docs, service_drive, title, content):
    """建立 Google Doc 並寫入 LLM 產生的內容"""
    try:
        # 1. 建立空白文件
        doc = service_docs.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')
        
        # 2. 寫入內容 (簡單插入)
        requests = [
            {'insertText': {'location': {'index': 1}, 'text': content}}
        ]
        service_docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        
        # 3. 取得連結
        file_info = service_drive.files().get(fileId=doc_id, fields='webViewLink').execute()
        return doc_id, file_info.get('webViewLink')
    except Exception as e:
        st.error(f"建立文件失敗: {e}")
        return None, None

def share_file_permissions(service_drive, file_id, emails):
    """將檔案權限分享給組員 (Writer)"""
    for email in emails:
        user_permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email.strip()
        }
        try:
            service_drive.permissions().create(
                fileId=file_id,
                body=user_permission,
                fields='id',
                sendNotificationEmail=False
            ).execute()
        except Exception as e:
            st.warning(f"⚠️ 無法分享給 {email} (可能是無效信箱): {e}")

def send_gmail(service_gmail, to_emails, subject, content):
    """寄送 Email 給組員"""
    for email in to_emails:
        try:
            message = MIMEText(content)
            message['to'] = email
            message['subject'] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {'raw': raw}
            service_gmail.users().messages().send(userId='me', body=body).execute()
        except Exception as e:
            st.error(f"❌ 寄信給 {email} 失敗: {e}")