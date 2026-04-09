import requests
import telebot
from flask import Flask
# from config import API_TOKEN # Bot Token ពី BotFather
API_TOKEN = "8689939123:AAFMTOGsozwBnrtvp0Ow63M6RwCP-r1lkWA"
bot = telebot.TeleBot(API_TOKEN)
app = Flask('')
from deep_translator import GoogleTranslator

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # Render ផ្ដល់ Port ឱ្យតាមរយៈ Environment Variable
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# ... កូដ Bot របស់អ្នក ...


def translate_to_khmer(text):
    try:
        # បកប្រែពីចិន (zh-CN) ឬអង់គ្លេស (en) ទៅខ្មែរ (km)
        # ប្រើ source='auto' ដើម្បីឱ្យវាស្គាល់ភាសាដោយស្វ័យប្រវត្តិ
        translated = GoogleTranslator(source='auto', target='km').translate(text)
        return translated
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

# ប្រើក្នុង Bot របស់អ្នក
# status_kh = translate_to_khmer(latest_track['TrackName'])

# មុខងារសម្រាប់ទាញយកទិន្នន័យពី API
def get_tracking_info(tracking_number):
    url = 'https://ycserver.zq-zn.com/api/Track/QueryWayBillTrackbyExternal'
    
    # Payload របស់អ្នក
    data = {
        'Token': 'CbiGueAfei8B%2BBlh/7Mwcoa/0OFvoDPD2nxApVDZHZv87840gcNtAGUgeffQHXlUH23pQSgdtir4miZpe2JsObqXrR8mZyp5htArz1/fWp2ca/tw0OIlt%2BYNnCrLNrzZL%2BnHjte9dL/LVzj1zXSxsUoNMvZOu5BZliX7s26/GwBDbWWOXSfHW6tKtw1bgTf%2B6S%2BVyoQRc52Q7t6yeIgbSf/aEOTNPCg1PbXJzjJH1D9z2w1TS0W9ylLuYeuOUeZAdqFAQFR3ouzm13P1VqGUlN9gQcsCC5VQNEaoxxmfASk=',
        'TrackKeywords': tracking_number,
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('data') and len(result['data']) > 0:
                return result['data'][0] # យកទិន្នន័យចុងក្រោយគេ
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# នៅពេលអ្នកប្រើផ្ញើពាក្យ /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "សួស្តី! សូមផ្ញើ **លេខកូដតាមដាន (Tracking Number)** មកកាន់ខ្ញុំ ដើម្បីពិនិត្យទីតាំងអីវ៉ាន់។")

# នៅពេលអ្នកប្រើផ្ញើលេខ Tracking (អត្ថបទធម្មតា)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    track_code = message.text.strip()
    bot.send_message(message.chat.id, "🔎 កំពុងស្វែងរកទិន្នន័យ...")
    
    latest_track = get_tracking_info(track_code)
    
    if latest_track:
        location = latest_track['Location'] if latest_track['Location'] else "មិនមានបញ្ជាក់"
        
        khmer_message = (
            f"📦 **ព័ត៌មានការដឹកជញ្ជូន**\n"
            f"--------------------------\n"
            f"🔢 លេខកូដ: `{latest_track['TrackCode']}`\n"
            f"📍 ទីតាំង: {translate_to_khmer(location)}\n"
            f"ℹ️ ស្ថានភាព: {translate_to_khmer(latest_track['TrackEnName'])}\n"
            f"🇨🇳 (ចិន): {translate_to_khmer(latest_track['TrackName'])}\n"
            f"⏰ កាលបរិច្ឆេទ: {translate_to_khmer(latest_track['CreateDate'])}\n"
            f"--------------------------\n"
            f"📢 ស្ថានភាពចុងក្រោយ: អីវ៉ាន់កំពុងស្ថិតក្នុងដំណាក់កាល {translate_to_khmer(latest_track['TrackEnName'])}"
        )
        bot.send_message(message.chat.id, khmer_message, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ សុំទោស! រកមិនឃើញទិន្នន័យសម្រាប់លេខកូដនេះទេ។")

# បញ្ជាឱ្យ Bot ដំណើរការជាប់រហូត
if __name__ == "__main__":
    # បើក Flask ក្នុង Thread ផ្សេងមួយទៀត
    threading.Thread(target=run_flask).start()
    
    # ចាប់ផ្ដើម Bot
    print("Bot is starting...")
    bot.remove_webhook()
    bot.infinity_polling()
