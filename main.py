import os
import threading
import requests
import telebot
from flask import Flask
from deep_translator import GoogleTranslator

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

def get_khmer_status(item):
    cn_text = item.get('TrackName', '') or ""
    en_text = item.get('TrackEnName', '') or ""
    
    # ជំហានទី ១: ឆែកក្នុង Dictionary ជាមុន (លទ្ធផលដូចក្នុងរូបភាពទី ១)
    for key in TRANS_DICT:
        if key in cn_text or key in en_text:
            # បើរកឃើញពាក្យគន្លឹះ ប្រើពាក្យក្នុង Dictionary
            # យើងអាចប្រើ Google Translator បន្ថែមដើម្បីបកប្រែផ្នែកដែលនៅសល់ (ដូចជាថ្ងៃខែក្នុងឃ្លា)
            try:
                source_text = cn_text if cn_text else en_text
                translated = GoogleTranslator(source='auto', target='km').translate(source_text)
                return translated
            except:
                return TRANS_DICT[key]
    
    # ជំហានទី ២: បើគ្មានក្នុង Dictionary ទេ ប្រើ Translator ទាំងស្រុង
    try:
        source_text = cn_text if cn_text else en_text
        if source_text:
            return GoogleTranslator(source='auto', target='km').translate(source_text)
    except:
        pass
        
    return cn_text if cn_text else en_text

# ៣. Flask App
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
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

# ៥. ការបង្ហាញលទ្ធផល
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "សូមផ្ញើលេខ Tracking ដើម្បីមើលព័ត៌មានលម្អិត។")

@bot.message_handler(func=lambda m: True)
def handle_track(message):
    track_code = message.text.strip()
    msg_wait = bot.send_message(message.chat.id, "🔎 កំពុងទាញយកទិន្នន័យ...")
    
    data_list = get_all_tracking(track_code)
    
    if data_list:
        h = data_list[0]
        # រៀបចំ Header តាមរូបភាព
        response = f"📋 **ម៉ាកុស:** {h.get('Marks', '---')}\n"
        response += f"🔢 **លេខវិក្កយបត្រ:** `{h.get('TrackCode', '---')}`\n"
        response += f"🚛 **លេខទូកុងតឺន័រ:** {h.get('InsideNO', '---')}\n"
        response += f"--------------------------\n\n"
        
        for i, item in enumerate(data_list):
            icon = "🟢" if i == 0 else "⚪️"
            line = "┃" if i < len(data_list) - 1 else " "
            
            date_str = item.get('CreateDate', '').split()[0]
            kh_status = get_khmer_status(item)
            en_sub = item.get('TrackEnName', '') 

            response += f"{icon} **{date_str}**\n"
            response += f"┃  **{kh_status}**\n"
            if en_sub: response += f"┃  `{en_sub}`\n"
            response += f"{line}\n"
            
        bot.edit_message_text(response, message.chat.id, msg_wait.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ រកមិនឃើញទិន្នន័យទេ។", message.chat.id, msg_wait.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    print("Bot is online with Hybrid Translation...")
    bot.infinity_polling()
