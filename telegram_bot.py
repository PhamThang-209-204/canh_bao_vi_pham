import requests
import threading

# 🔑 Cấu hình tại đây
TOKEN = "8384672776:AAHu12MkW_5nFCOntd7gABJdipoNOFUEqW0"   # ← token ví dụ
CHAT_ID = "5990406025"                       # ← chat_id của bạn

def send_telegram_photo_sync(photo_path, caption=""):
    """
    Gửi ảnh đồng bộ (chặn luồng chính)
    """
    if not TOKEN or not CHAT_ID:
        return
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            payload = {"chat_id": CHAT_ID, "caption": caption}
            files = {"photo": photo}
            response = requests.post(url, data=payload, files=files, timeout=10)
            if response.status_code != 200:
                print(f"[Telegram Error] {response.text}")
            else:
                print(f"[Telegram] Da gui thong bao vi pham thanh cong!")
    except Exception as e:
        print(f"[Telegram Exception] {e}")

def send_telegram_photo(photo_path, caption=""):
    """
    Gửi ảnh bất đồng bộ (không làm lag video)
    """
    if not TOKEN or not CHAT_ID:
        return
        
    thread = threading.Thread(
        target=send_telegram_photo_sync, 
        args=(photo_path, caption)
    )
    thread.daemon = True
    thread.start()


# 🔥 TEST thử luôn (đã đóng để không bị lỗi lúc import)
# send_telegram_photo("violation.jpg", "🚗 Test gửi ảnh vi phạm")