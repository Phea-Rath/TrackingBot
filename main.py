import os
import time
import threading
import html
import requests
import telebot
from flask import Flask
try:
    from googletrans import Translator
    translator = Translator()
except Exception as e:
    translator = None

# ១. ការកំណត់ Bot Token
API_TOKEN = "8689939123:AAFMTOGsozwBnrtvp0Ow63M6RwCP-r1lkWA"
bot = telebot.TeleBot(API_TOKEN)

# ២. វចនានុក្រមបកប្រែយោងតាមរូបភាព (Technical Logistics Dictionary)
# យើងដកលេខថ្ងៃខែចេញ ដើម្បីឱ្យវា Match ជាមួយស្ថានភាពទូទៅបានគ្រប់ពេល
TRANS_DICT = {
    # ស្ថានភាពចុងក្រោយ (Final Status)
    "到达仓库已拆柜": "មកដល់ឃ្លាំងហើយ និងបានរើចេញពីកុងតឺន័ររួចរាល់",
    "Unloaded": "ទំនិញត្រូវបានទម្លាក់ពីទូ (Unloaded)",
    
    # ស្ថានភាពកំពង់ផែ និងព្រំដែន
    "到达目的港口 已抵达边境，预计今明晚到仓": "មកដល់កំពង់ផែគោលដៅ (បានមកដល់ព្រំដែនហើយ ត្រៀមដល់ឃ្លាំងនៅយប់នេះ ឬស្អែក)",
    "到达目的港口": "មកដល់កំពង់ផែគោលដៅ",
    "Arrival Desitination port": "មកដល់កំពង់ផែគោលដៅ",
    
    # ស្ថានភាពដឹកជញ្ជូន
    "运输途中请稍等": "សូមរង់ចាំ ក្នុងអំឡុងពេលដឹកជញ្ជូន",
    "on the way": "កំពុងស្ថិតនៅលើផ្លូវដឹកជញ្ជូន",
    "预计": "រំពឹងថានឹង",
    "过境": "ឆ្លងកាត់ព្រំដែន",
    "到仓": "មកដល់ឃ្លាំង",
    "到港": "មកដល់កំពង់ផែ",
    
    # ស្ថានភាពគយ
    "报关已放行": "សេចក្តីប្រកាសពន្ធគយត្រូវបានបញ្ចេញផ្សាយ",
    "Customs released": "សេចក្តីប្រកាសពន្ធគយត្រូវបានបញ្ចេញផ្សាយ",
    "广州转关放行": "ក្វាងចូវត្រូវបានបញ្ចេញផ្សាយឡើងវិញ",
    "报关中": "សេចក្តីប្រកាសគយ កំពុងដំណើរការ",
    "Customs declaration in progress": "សេចក្តីប្រកាសគយ កំពុងដំណើរការ",
    
    # ស្ថានភាពដំបូង
    "装柜完成": "ការវេចខ្ចប់ និងដាក់ចូលទូកុងតឺន័របានរួចរាល់",
    "The container finish": "ការបញ្ចប់ក្នុងទូ",
    "运单已入库准备发运": "វិក្កយបត្រត្រូវបានដាក់ចូលក្នុងឃ្លាំង និងត្រៀមសម្រាប់ការដឹកជញ្ជូន",
    "Waybill has been processed": "វិក្កយបត្រត្រូវបានកែច្នៃ",
    "China": "ប្រទេសចិន"
}

def translate_cloud(text, src='zh-CN', target='km'):
    if not text:
        return ""
    # ១. សាកល្បងប្រើ Google Translator (សម្រាប់ Local)
    if translator:
        try:
            res = translator.translate(text, dest=target).text
            if res:
                return res
        except Exception:
            pass

    # ២. បើ Google ស្ទះ/Block លើ Render (Datacenter IP Block) ប្រើ MyMemory API
    try:
        url = 'https://api.mymemory.translated.net/get'
        params = {'q': text, 'langpair': f'{src}|{target}'}
        res = requests.get(url, params=params, timeout=5).json()
        translated = res.get('responseData', {}).get('translatedText', '')
        if translated and 'MYMEMORY' not in translated.upper() and 'INVALID' not in translated.upper():
            return translated
    except Exception:
        pass

    return ""

def get_khmer_status(item):
    cn_text = item.get('TrackName', '') or ""
    en_text = item.get('TrackEnName', '') or ""
    
    # ជំហានទី ១: ឆែកក្នុង Dictionary ជាមុន (លទ្ធផលត្រឹមត្រូវតាមបច្ចេកទេស)
    for key in TRANS_DICT:
        if key in cn_text or key in en_text:
            return TRANS_DICT[key]
    
    # ជំហានទី ២: បើគ្មានក្នុង Dictionary ទេ ប្រើ Online Translator (Google + MyMemory Cloud Fallback)
    source_text = cn_text if cn_text else en_text
    src_lang = 'zh-CN' if cn_text else 'en'
    
    if source_text:
        translated = translate_cloud(source_text, src=src_lang, target='km')
        if translated:
            return translated
        
    return source_text

# ៣. Flask App
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)

# ៤. មុខងារទាញយកទិន្នន័យ
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

# ៥. មុខងារ Animated Loading
def animate_loading(chat_id, message_id, stop_event):
    frames = [
        "⚡ <b>កំពុងស្វែងរកទិន្នន័យ​ និងបកប្រែជាភាសាខ្មែរ</b> <code>.</code>",
        "⚡ <b>កំពុងស្វែងរកទិន្នន័យ​ និងបកប្រែជាភាសាខ្មែរ</b> <code>..</code>",
        "⚡ <b>កំពុងស្វែងរកទិន្នន័យ​ និងបកប្រែជាភាសាខ្មែរ</b> <code>...</code>",
        "⚡ <b>កំពុងស្វែងរកទិន្នន័យ​ និងបកប្រែជាភាសាខ្មែរ</b> <code>....</code>",
    ]
    idx = 0
    while not stop_event.is_set():
        time.sleep(0.6)
        if stop_event.is_set():
            break
        idx = (idx + 1) % len(frames)
        try:
            bot.edit_message_text(frames[idx], chat_id, message_id, parse_mode="HTML")
        except Exception:
            pass

# ៦. ការបង្ហាញលទ្ធផល
@bot.message_handler(commands=['start'])
def start(message):
    welcome_msg = (
        "✨ <b>សូមស្វាគមន៍មកកាន់ Tracking Bot!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📦 សូមផ្ញើ <b>លេខ Tracking / វិក្កយបត្រ</b> របស់អ្នក ដើម្បីពិនិត្យមើលព័ត៌មានដឹកជញ្ជូនលម្អិត។"
    )
    bot.reply_to(message, welcome_msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_track(message):
    track_code = message.text.strip()
    msg_wait = bot.send_message(
        message.chat.id, 
        "⚡ <b>កំពុងស្វែងរកទិន្នន័យ​ និងបកប្រែជាភាសាខ្មែរ</b> <code>.</code>", 
        parse_mode="HTML"
    )
    
    stop_event = threading.Event()
    anim_thread = threading.Thread(
        target=animate_loading, 
        args=(message.chat.id, msg_wait.message_id, stop_event), 
        daemon=True
    )
    anim_thread.start()

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        data_list = get_all_tracking(track_code)
        
        if data_list:
            h = data_list[0]
            marks = html.escape(str(h.get('Marks', '---')))
            code = html.escape(str(h.get('TrackCode', '---')))
            inside_no = html.escape(str(h.get('InsideNO', '---')))

            # Modern Card Header Layout
            response = "📦 <b>ព័ត៌មានការដឹកជញ្ជូន (Tracking Info)</b>\n"
            response += "━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"🏷️ <b>ម៉ាកុស:</b> <code>{marks}</code>\n"
            response += f"🧾 <b>លេខវិក្កយបត្រ:</b> <code>{code}</code>\n"
            response += f"🚛 <b>លេខទូកុងតឺន័រ:</b> <code>{inside_no}</code>\n"
            response += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            response += "📍 <b>ដំណាក់កាលដឹកជញ្ជូន (Timeline):</b>\n\n"
            
            for i, item in enumerate(data_list):
                status_icon = "🟢" if i == 0 else "▫️"
                date_str = html.escape(str(item.get('CreateDate', '')).split()[0])
                kh_status = html.escape(get_khmer_status(item))
                en_sub = html.escape(str(item.get('TrackEnName', '') or ""))

                response += f"{status_icon} <b>{date_str}</b>\n"
                response += f" ┗ <b>{kh_status}</b>\n"
                if en_sub:
                    response += f" └ <i>{en_sub}</i>\n"
                response += "\n"
                
            stop_event.set()
            anim_thread.join(timeout=1.0)
            bot.edit_message_text(response, message.chat.id, msg_wait.message_id, parse_mode="HTML")
        else:
            stop_event.set()
            anim_thread.join(timeout=1.0)
            bot.edit_message_text("❌ <b>រកមិនឃើញទិន្នន័យទេ។</b>", message.chat.id, msg_wait.message_id, parse_mode="HTML")
    except Exception as e:
        stop_event.set()
        anim_thread.join(timeout=1.0)
        bot.edit_message_text("⚠️ <b>មានបញ្ហាក្នុងការទាញយកទិន្នន័យ។</b>", message.chat.id, msg_wait.message_id, parse_mode="HTML")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    print("Bot is online with Hybrid Translation...")
    bot.infinity_polling()

