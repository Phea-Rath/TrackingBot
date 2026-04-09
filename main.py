import os
import threading
import requests
import telebot
from flask import Flask

# ១. ការកំណត់ Bot Token
API_TOKEN = "8689939123:AAFMTOGsozwBnrtvp0Ow63M6RwCP-r1lkWA"
bot = telebot.TeleBot(API_TOKEN)

# ២. វចនានុក្រមបកប្រែ (Dictionary Mapping) ផ្អែកលើ JSON របស់អ្នក
TRANS_DICT = {
    "Unloaded": "អីវ៉ាន់មកដល់ឃ្លាំង និងបានរើចេញពីកុងតឺន័រហើយ",
    "Arrival Desitination port": "មកដល់កំពង់ផែគោលដៅ (បានដល់ព្រំដែន ត្រៀមដល់ឃ្លាំង)",
    "on the way ,China": "កំពុងដឹកជញ្ជូនក្នុងប្រទេសចិន (រង់ចាំការឆ្លងកាត់ព្រំដែន)",
    "Customs released ,China": "ទំនិញត្រូវបានបញ្ចេញពីគយ (ចិន)",
    "Customs declaration in progress": "កំពុងស្ថិតក្នុងដំណាក់កាលរៀបចំឯកសារគយ",
    "The container finish": "ការរៀបចំវេចខ្ចប់ចូលកុងតឺន័របានរួចរាល់",
    "Waybill has been processed   China": "វិក្កយបត្រត្រូវបានបញ្ចូលក្នុងប្រព័ន្ធ និងត្រៀមចេញដំណើរ",
    "China": "ប្រទេសចិន",
    "": "មិនមានបញ្ជាក់"
}

def get_khmer(text):
    if not text: return "មិនមានទិន្នន័យ"
    # សម្អាត space និងទាញយកពាក្យបកប្រែ បើមិនមានក្នុង list ទេ ឱ្យបង្ហាញអក្សរដើម
    return TRANS_DICT.get(text.strip(), text)

# ៣. Flask App សម្រាប់ Render
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# ៤. មុខងារទាញយកទិន្នន័យទាំងអស់ (List of Data)
def get_all_tracking(track_number):
    url = 'https://ycserver.zq-zn.com/api/Track/QueryWayBillTrackbyExternal'
    data = {
        'Token': 'CbiGueAfei8B%2BBlh/7Mwcoa/0OFvoDPD2nxApVDZHZv87840gcNtAGUgeffQHXlUH23pQSgdtir4miZpe2JsObqXrR8mZyp5htArz1/fWp2ca/tw0OIlt%2BYNnCrLNrzZL%2BnHjte9dL/LVzj1zXSxsUoNMvZOu5BZliX7s26/GwBDbWWOXSfHW6tKtw1bgTf%2B6S%2BVyoQRc52Q7t6yeIgbSf/aEOTNPCg1PbXJzjJH1D9z2w1TS0W9ylLuYeuOUeZAdqFAQFR3ouzm13P1VqGUlN9gQcsCC5VQNEaoxxmfASk=',
        'TrackKeywords': track_number,
    }
    try:
        res = requests.post(url, json=data, timeout=10)
        if res.status_code == 200:
            return res.json().get('data', [])
        return []
    except: return []

# ៥. ការបង្ហាញលទ្ធផលជា Timeline
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "សូមផ្ញើលេខ Tracking ដើម្បីមើលព័ត៌មានលម្អិត។")

@bot.message_handler(func=lambda m: True)
def handle_track(message):
    track_code = message.text.strip()
    msg_wait = bot.send_message(message.chat.id, "🔎 កំពុងស្វែងរកទិន្នន័យ...")
    
    data_list = get_all_tracking(track_code)
    
    if data_list:
        # ព័ត៌មានក្បាលលើ (Header)
        header = data_list[0]
        response = f"📋 **លេខកូដ:** `{header['TrackCode']}`\n"
        response += f"📦 **សញ្ញាសម្គាល់:** {header['Marks']}\n"
        response += f"🚚 **លេខទូ:** {header['InsideNO']}\n"
        response += f"--------------------------\n\n"
        
        # បង្កើត Timeline
        for i, item in enumerate(data_list):
            icon = "🟢" if i == 0 else "⚪️" # ចំណុចបៃតងសម្រាប់ស្ថានភាពចុងក្រោយ
            connector = "┃\n" if i < len(data_list) - 1 else ""
            
            date_str = item['CreateDate'].split()[0] # យកតែថ្ងៃខែឆ្នាំ
            status_kh = get_khmer(item['TrackEnName'])
            
            response += f"{icon} **{date_str}**\n"
            response += f"┗ {status_kh}\n"
            response += f"{connector}"
            
        bot.edit_message_text(response, message.chat.id, msg_wait.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ រកមិនឃើញទិន្នន័យទេ។", message.chat.id, msg_wait.message_id)

# ៦. ដំណើរការ
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    print("Bot is online...")
    bot.infinity_polling()
