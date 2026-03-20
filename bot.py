import os
import io
from flask import Flask, request, jsonify
from PIL import Image
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ.get("7833088741:AAG7qDgQ4Qe81lxvDeQkOjdnSteuJv1NhOg")
WIDTH = 135
HEIGHT = 240

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_photo(chat_id, photo_bytes, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {"photo": photo_bytes}
    data = {"chat_id": chat_id, "caption": caption}
    requests.post(url, files=files, data=data)

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if "message" not in data:
        return jsonify({"ok": True})
    
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    
    if "text" in msg and msg["text"] == "/start":
        send_message(chat_id, f"Пришли фото, сделаю {WIDTH}x{HEIGHT} для M5StickC Plus 2!")
        return jsonify({"ok": True})
    
    if "photo" in msg:
        try:
            photo = msg["photo"][-1]
            file_id = photo["file_id"]
            
            file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile", 
                                     params={"file_id": file_id}).json()
            file_path = file_info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            
            img_data = requests.get(file_url).content
            img = Image.open(io.BytesIO(img_data))
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            target_ratio = WIDTH / HEIGHT
            w, h = img.size
            
            if w / h > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                img = img.crop((left, 0, left + new_w, h))
            else:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                img = img.crop((0, top, w, top + new_h))
            
            img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=65, optimize=True)
            output.seek(0)
            
            size_kb = len(output.getvalue()) / 1024
            send_photo(chat_id, output, f"✅ {WIDTH}x{HEIGHT} | {size_kb:.1f} KB")
            
        except Exception as e:
            send_message(chat_id, f"Ошибка: {str(e)}")
    
    return jsonify({"ok": True})

@app.route('/')
def index():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
