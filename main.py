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
    # --- ស្ថានភាពជាភាសាចិន ---
    "到达仓库已拆柜": "មកដល់ឃ្លាំងហើយ និងបានរើចេញពីកុងតឺន័ររួចរាល់",
    "到达目的港口 已抵达边境，预计今明晚到仓": "មកដល់កំពង់ផែគោលដៅ (បានដល់ព្រំដែនហើយ ត្រៀមដល់ឃ្លាំងក្នុងពេលឆាប់ៗ)",
    "运输途中请稍等 更新：预计4-10到港,China": "កំពុងដឹកជញ្ជូន រង់ចាំការអាប់ដេត៖ រំពឹងថានឹងដល់កំពង់ផែនៅថ្ងៃទី ៤-១០, ប្រទេសចិន",
    "运输途中请稍等 预计4-10到港,China": "កំពុងដឹកជញ្ជូន រំពឹងថានឹងដល់កំពង់ផែនៅថ្ងៃទី ៤-១០, ប្រទេសចិន",
    "运输途中请稍等 预计4-3过境，预计4-4到仓,China": "កំពុងដឹកជញ្ជូន រំពឹងថានឹងឆ្លងកាត់ព្រំដែនថ្ងៃ ៤-៣ និងដល់ឃ្លាំងថ្ងៃ ៤-៤, ប្រទេសចិន",
    "报关已放行 更新：预计4-3开船，航期7天左右,China": "គយបានបញ្ចេញទំនិញ អាប់ដេត៖ រំពឹងថានឹងចេញកប៉ាល់ថ្ងៃ ៤-៣ រយៈពេលដឹកជញ្ជូនប្រហែល ៧ ថ្ងៃ, ប្រទេសចិន",
    "报关已放行 更新：预计4-3开船，航期7天,China": "គយបានបញ្ចេញទំនិញ អាប់ដេត៖ រំពឹងថានឹងចេញកប៉ាល់ថ្ងៃ ៤-៣ រយៈពេលដឹកជញ្ជូន ៧ ថ្ងៃ, ប្រទេសចិន",
    "报关已放行 ,China": "គយបានបញ្ចេញទំនិញរួចរាល់, ប្រទេសចិន",
    "报关已放行 广州转关放行,China": "គយបានបញ្ចេញទំនិញរួចរាល់ (ក្វាងចូវ), ប្រទេសចិន",
    "报关中": "កំពុងស្ថិតក្នុងដំណាក់កាលរៀបចំឯកសារគយ",
    "装柜完成": "ការវេចខ្ចប់ និងរៀបចំដាក់ចូលទូកុងតឺន័របានរួចរាល់",
    "运单已入库准备发运,China": "វិក្កយបត្រត្រូវបានបញ្ចូលក្នុងប្រព័ន្ធ និងត្រៀមចេញដំណើរ, ប្រទេសចិន",

    # --- ស្ថានភាពជាភាសាអង់គ្លេស ---
    "Unloaded": "រើចេញពីទូ (Unloaded)",
    "Arrival Desitination port": "មកដល់កំពង់ផែគោលដៅ",
    "on the way ,China": "កំពុងស្ថិតនៅលើផ្លូវដឹកជញ្ជូន, ប្រទេសចិន",
    "Customs released ,China": "គយបានបញ្ចេញទំនិញរួចរាល់",
    "Customs declaration in progress": "កំពុងរៀបចំឯកសារគយ",
    "The container finish": "ការវេចខ្ចប់ក្នុងទូបានបញ្ចប់",
    "Waybill has been processed China": "វិក្កយបត្រត្រូវបានរៀបចំរួចរាល់, ប្រទេសចិន",
    "Waybill has been processed   China": "វិក្កយបត្រត្រូវបានរៀបចំរួចរាល់, ប្រទេសចិន"
}

def get_khmer_status(item):
    cn_text = item.get('TrackName', '').strip()
    en_text = item.get('TrackEnName', '').strip()

    # ជាដំបូងឆែកមើលអក្សរចិន បើអត់មានទើបឆែកអក្សរអង់គ្លេស
    khmer_status = TRANS_DICT.get(cn_text) or TRANS_DICT.get(en_text)
    
    # ប្រសិនបើអត់មានក្នុង Dictionary ទាំងពីរទេ ឱ្យបង្ហាញអក្សរដើមដែលមាន
    if not khmer_status:
        khmer_status = cn_text if cn_text else en_text
        
    return khmer_status

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
            icon = "🟢" if i == 0 else "⚪️"
            connector = "┃" if i < len(data_list) - 1 else ""
            
            date_str = item.get('CreateDate', '').split()[0]
            kh_status = get_khmer_status(item)
            sub_text = item.get('TrackEnName', '') # បង្ហាញអង់គ្លេសពីក្រោមតូចៗ
        
            response += f"{icon} **{date_str}\n"
            response += f"┃  `**{kh_status}`\n" if kh_status else ""
            response += f"┃  `{sub_text}`\n" if sub_text else ""
            response += f"{connector}\n"
            
        bot.edit_message_text(response, message.chat.id, msg_wait.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ រកមិនឃើញទិន្នន័យទេ។", message.chat.id, msg_wait.message_id)

# ៦. ដំណើរការ
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.remove_webhook()
    print("Bot is online...")
    bot.infinity_polling()
