from __future__ import unicode_literals
from urllib import parse
import string
from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import json
import configparser
import os
import logging
# 1.setup log path and create log directory
logName = 'MyProgram.log'
logDir = 'log'
logPath = logDir + '/' + logName
# 1231321231231121131312

# create log directory
os.makedirs(logDir, exist_ok=True)

# 2.create logger, then setLevel
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)

# 3.create file handler, then setLevel
# create file handler
fileHandler = logging.FileHandler(logPath, mode='w')
fileHandler.setLevel(logging.DEBUG)

# 4.create stram handler, then setLevel
# create stream handler
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)

# 5.create formatter, then handler setFormatter
AllFormatter = logging.Formatter(
    '[%(levelname)s][%(asctime)s][LINE:%(lineno)s][%(module)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(AllFormatter)
streamHandler.setFormatter(AllFormatter)

# 6.logger addHandler
logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

app = Flask(__name__, static_url_path='/static')
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])


config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
my_line_id = config.get('line-bot', 'my_line_id')
end_point = config.get('line-bot', 'end_point')
line_login_id = config.get('line-bot', 'line_login_id')
line_login_secret = config.get('line-bot', 'line_login_secret')
my_phone = config.get('line-bot', 'my_phone')
HEADER = {
    'Content-type': 'application/json',
    'Authorization': f'Bearer {config.get("line-bot", "channel_access_token")}'
}

key_city = ['基隆市天氣', '嘉義市天氣', '臺北市天氣', '台北市天氣', '嘉義縣天氣', '新北市天氣', '臺南市天氣', '台南市天氣', '桃園縣天氣', '高雄市天氣', '新竹市天氣', '屏東縣天氣',
            '新竹縣天氣', '臺東縣天氣', '台東縣天氣', '苗栗縣天氣', '花蓮縣天氣', '臺中市天氣', '台中市天氣', '宜蘭縣天氣', '彰化縣天氣', '澎湖縣天氣', '南投縣天氣', '金門縣天氣', '雲林縣天氣', '連江縣天氣']


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'GET':
        return 'ok'
    body = request.json
    events = body["events"]
    if request.method == 'POST' and len(events) == 0:
        return 'ok'
    logger.info(body)
    print(body)
    if "replyToken" in events[0]:
        payload = dict()
        replyToken = events[0]["replyToken"]
        payload["replyToken"] = replyToken
        if events[0]["type"] == "message":
            if events[0]["message"]["type"] == "text":
                text = events[0]["message"]["text"]

                if text == "我的名字":
                    payload["messages"] = [getNameEmojiMessage()]
                elif text == "出去玩囉":
                    payload["messages"] = [getPlayStickerMessage()]
                elif text == "台北101":
                    payload["messages"] = [getTaipei101ImageMessage(),
                                           getTaipei101LocationMessage(),
                                           getMRTVideoMessage()
                                           ]
                elif text == "quoda":
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": getTotalSentMessageCount()
                        }
                    ]
                elif text in key_city:
                    if text[0] == '台':
                        text = text.replace('台', '臺')
                    user_city = text[:3]
                    weather = getWeather(user_city)
                    msg_weaterInfo = transferWeatherData(weather)
                    line_bot_api.reply_message(
                        replyToken, TextSendMessage(text=msg_weaterInfo))
                    print('transferWeatherData: success')
                    payload["messages"] = [
                        {
                            "type": "text",
                            # "text": getWeather(city)
                        }
                    ]
                elif text == "今日確診人數":
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": getTodayCovid19Message()
                        }
                    ]
                elif text == "主選單":
                    payload["messages"] = [
                        {
                            "type": "template",
                            "altText": "This is a buttons template",
                            "template": {
                                    "type": "buttons",
                                    "title": "Menu",
                                    "text": "Please select",
                                    "actions": [
                                        {
                                            "type": "message",
                                            "label": "我的名字",
                                            "text": "我的名字"
                                        },
                                        {
                                            "type": "message",
                                            "label": "今日確診人數",
                                            "text": "今日確診人數"
                                        },
                                        {
                                            "type": "uri",
                                            "label": "聯絡我",
                                            "uri": f"tel:{my_phone}"
                                        }
                                    ]
                            }
                        }
                    ]
                else:
                    payload["messages"] = [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                replyMessage(payload)
            elif events[0]["message"]["type"] == "location":
                logger.info(events[0]["message"])
                title = events[0]["message"]["title"]
                latitude = events[0]["message"]["latitude"]
                longitude = events[0]["message"]["longitude"]
                payload["messages"] = [
                    getLocationConfirmMessage(title, latitude, longitude)]
                logger.info(payload)
                replyMessage(payload)
        elif events[0]["type"] == "postback":
            if "params" in events[0]["postback"]:
                reservedTime = events[0]["postback"]["params"]["datetime"].replace(
                    "T", " ")
                payload["messages"] = [
                    {
                        "type": "text",
                        "text": F"已完成預約於{reservedTime}的叫車服務"
                    }
                ]
                replyMessage(payload)
            else:
                data = json.loads(events[0]["postback"]["data"])
                logger.info(data)
                action = data["action"]
                if action == "get_near":
                    data["action"] = "get_detail"
                    payload["messages"] = [getCarouselMessage(data)]
                elif action == "get_detail":
                    del data["action"]
                    payload["messages"] = [getTaipei101ImageMessage(),
                                           getTaipei101LocationMessage(),
                                           getMRTVideoMessage(),
                                           getCallCarMessage(data)]
                replyMessage(payload)

    return 'OK'

# 有人來call這個路徑，就執行def callback


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 若有接收到MessageEvent的話，call這裡


@handler.add(MessageEvent, message=TextMessage)
def pretty_echo(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


@app.route("/sendTextMessageToMe", methods=['POST'])
def sendTextMessageToMe():
    pushMessage({})
    return 'OK'


def getWeather(city):
    token = 'CWB-5903F8B2-FC6A-4703-9440-01FDFD7B64B2'
    url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWB-5903F8B2-FC6A-4703-9440-01FDFD7B64B2'
    Data = requests.get(url)
    locations = (json.loads(Data.text)
                 )['records']['location']
    # FIND CITY
    try:
        i = 0
        while (i <= (len(locations))):
            if (locations[i]["locationName"] == city):
                item = locations[i]
                break
            i += 1
        return item

    except IndexError:
        print('you get IndexError: list index out of range')
        return 'no data'


def transferWeatherData(item):
    cityName = item["locationName"]

    weatherElement = item["weatherElement"]  # 取得該縣市的天氣資料

# 天氣現象
    if (weatherElement[0]["elementName"] == 'Wx'):
        timeDicts = weatherElement[0]["time"]  # 依時間區段設定早晚跟明天
        Wx_morning = timeDicts[0]["parameter"]["parameterName"]
        Wx_night = timeDicts[1]["parameter"]["parameterName"]
        Wx_tomorrow = timeDicts[2]["parameter"]["parameterName"]

# 降雨機率
    if (weatherElement[1]["elementName"] == 'PoP'):
        timeDicts = weatherElement[1]["time"]  # 依時間區段設定早晚跟明天
        PoP_morning = str(timeDicts[0]["parameter"]["parameterName"]) + \
            timeDicts[0]["parameter"]["parameterUnit"]
        PoP_night = str(timeDicts[1]["parameter"]["parameterName"]) + \
            timeDicts[1]["parameter"]["parameterUnit"]
        PoP_tomorrow = str(timeDicts[2]["parameter"]["parameterName"]) + \
            timeDicts[2]["parameter"]["parameterUnit"]

# 低溫
    if (weatherElement[2]["elementName"] == 'MinT'):
        timeDicts = weatherElement[2]["time"]  # 依時間區段設定早晚跟明天
        MinT_morning = timeDicts[0]["parameter"]["parameterName"] + \
            timeDicts[0]["parameter"]["parameterUnit"]
        MinT_night = timeDicts[1]["parameter"]["parameterName"] + \
            timeDicts[1]["parameter"]["parameterUnit"]
        MinT_tomorrow = timeDicts[2]["parameter"]["parameterName"] + \
            timeDicts[2]["parameter"]["parameterUnit"]

# 舒適度
    if (weatherElement[3]["elementName"] == 'CI'):
        timeDicts = weatherElement[3]["time"]  # 依時間區段設定早晚跟明天
        CI_morning = timeDicts[0]["parameter"]["parameterName"]
        CI_night = timeDicts[1]["parameter"]["parameterName"]
        CI_tomorrow = timeDicts[2]["parameter"]["parameterName"]

# 高溫
    if (weatherElement[4]["elementName"] == 'MaxT'):
        timeDicts = weatherElement[4]["time"]  # 依時間區段設定早晚跟明天
        MaxT_morning = timeDicts[0]["parameter"]["parameterName"] + \
            timeDicts[0]["parameter"]["parameterUnit"]
        MaxT_night = timeDicts[1]["parameter"]["parameterName"] + \
            timeDicts[1]["parameter"]["parameterUnit"]
        MaxT_tomorrow = timeDicts[2]["parameter"]["parameterName"] + \
            timeDicts[2]["parameter"]["parameterUnit"]

        today = timeDicts[0]["startTime"].split(
            ",")
        tomorrow = timeDicts[2]["endTime"].split(
            ",")

    replyMsg = cityName + "今明兩日天氣預報:" + '\n' + \
        str(today[0][0:10]) + ":" + '\n' + Wx_morning + " " + CI_morning + '\n' + "白天高溫: " + MaxT_morning + '\n' + "今白天低溫: " + MinT_morning + '\n' + "白天下雨機率: " + PoP_morning + '\n' + "晚上高溫: " + MaxT_night + '\n' + "晚上低溫: " + \
        MinT_night + '\n' + "晚上下雨機率: " + PoP_night + '\n' + \
        str(tomorrow[0][0:10]) + ":" + '\n' + Wx_tomorrow + " " + CI_tomorrow + '\n' + "高溫: " + \
        MaxT_tomorrow + '\n' + "低溫: " + MinT_tomorrow + '\n' + "下雨機率: " + PoP_tomorrow

# 低溫提醒
# notice_minT()
    minT = min([weatherElement[2]["time"][0]["parameter"]["parameterName"], weatherElement[2]["time"]
                [1]["parameter"]["parameterName"], weatherElement[2]["time"][2]["parameter"]["parameterName"]])
# 高溫提醒
    maxT = max([weatherElement[4]["time"][0]["parameter"]["parameterName"], weatherElement[4]["time"]
                [1]["parameter"]["parameterName"], weatherElement[4]["time"][2]["parameter"]["parameterName"]])
    pop = max([weatherElement[1]["time"][0]["parameter"]["parameterName"], weatherElement[1]["time"]
               [1]["parameter"]["parameterName"], weatherElement[1]["time"][2]["parameter"]["parameterName"]])

    if (int(minT) < 10):
        replyMsg = replyMsg + "請注意低溫"
        return str(replyMsg)

    elif (int(maxT) > 36):
        replyMsg = replyMsg + "請注意高溫"
        return str(replyMsg)

    elif (int(pop) > 42):  # 降雨提醒 pop=12h/ pop6=6h
        replyMsg = replyMsg + '\n' + "請攜待雨具"
        return str(replyMsg)

    else:
        return replyMsg


def getNameEmojiMessage():
    lookUpStr = string.ascii_uppercase + string.ascii_lowercase
    productId = "5ac21a8c040ab15980c9b43f"
    name = "Harvey"
    message = dict()
    message['type'] = "text"
    message['text'] = "$" * len(name)
    emojis = list()
    for i, c in enumerate(name):
        emojis.append({
            "index": i,
            "productId": productId,
            "emojiId": f"{lookUpStr.index(c)+ 1}".zfill(3)
        })
    message['emojis'] = emojis
    return message


def getCarouselMessage(data):
    message = {
        "type": "template",
        "altText": "this is a image carousel template",
        "template": {
            "type": "image_carousel",
            "columns": [
              {
                "imageUrl": F"{end_point}/static/taipei_101.jpeg",
                "action": {
                    "type": "postback",
                    "label": "台北101",
                    "data": json.dumps(data)
                }
              },
                {
                  "imageUrl": F"{end_point}/static/02_shan.jpg",
                  "action": {
                      "type": "postback",
                      "label": "象山步道",
                      "data": json.dumps(data)
                  }
              },
                {
                    "imageUrl": F"{end_point}/static/03_yuanshan.jpg",
                    "action": {
                        "type": "postback",
                        "label": "圓山飯店",
                        "data": json.dumps(data)
                    }
              },
                {
                  "imageUrl": F"{end_point}/static/04_taipeizoo.jpg",
                    "action": {
                        "type": "postback",
                        "label": "台北動物園",
                        "data": json.dumps(data)
                    }
              },
                {
                  "imageUrl": F"{end_point}/static/05_nightmarket.jpg",
                  "action": {
                      "type": "postback",
                      "label": "饒河夜市",
                      "data": json.dumps(data)
                  }
              }
            ]
        }
    }
    return message


def getLocationConfirmMessage(title, latitude, longitude):
    data = {"latitude": latitude, "longitude": longitude,
            "title": title, "action": "get_near"}
    message = {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
                "type": "confirm",
                "text": f"是否要搜尋 {title} 附近的景點？",
                "actions": [
                    {
                        "type": "postback",
                        "label": "是",
                        "data": json.dumps(data),
                        "displayText": "是",
                    },
                    {
                        "type": "message",
                        "label": "否",
                        "text": "否"
                    }
                ]
        }
    }
    return message


def getPlayStickerMessage():
    message = {
        "type": "sticker",
        "packageId": "446",
        "stickerId": "1988"
    }
    return message


def getTaipei101LocationMessage():
    message = {
        "type": "location",
        "title": "Taipei 101",
        "address": "台北市信義區信義路五段7號89樓",
        "latitude": 25.034804599999998,
        "longitude": 121.5655868
    }
    return message


def getMRTVideoMessage(originalContentUrl=F"{end_point}/static/taipei_101_video.mp4"):
    message = {
        "type": "video",
        "originalContentUrl": F"{end_point}/static/taipei_101_video.mp4",
        "previewImageUrl": F"{end_point}/static/taipei_101.jpeg",
        "trackingId": "track-id"
    }
    return message


def getMRTSoundMessage():
    message = dict()
    message["type"] = "audio"
    message["originalContentUrl"] = F"{end_point}/static/mrt_sound.m4a"
    import audioread
    with audioread.audio_open('static/mrt_sound.m4a') as f:
        # totalsec contains the length in float
        totalsec = f.duration
    message["duration"] = totalsec * 1000
    return message


def getTaipei101ImageMessage(originalContentUrl=F"{end_point}/static/taipei_101.jpeg"):

    return getImageMessage(originalContentUrl)


def getImageMessage(originalContentUrl):
    message = {
        "type": "image",
        "originalContentUrl": originalContentUrl,
        "previewImageUrl": originalContentUrl
    }
    return message


def replyMessage(payload):
    response = requests.post(
        "https://api.line.me/v2/bot/message/reply", headers=HEADER, json=payload)
    print(response.text)
    print('payload =', payload)
    return 'OK'


def pushMessage(payload):
    response = requests.post(
        "https://api.line.me/v2/bot/message/push", headers=HEADER, json=payload)
    print(response.text)
    return 'OK'


def getTotalSentMessageCount():
    response = {}
    return 0


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    app.debug = True
    app.run()


# def getCallCarMessage(data):
#     message = {
#         "type": "template",
#         "altText": "this is a template",
#         "template": {
#             "type": "buttons",
#             "text": f"請選擇至 {data['title']} 預約叫車時間",
#             "actions": [
#               {
#                   "type": "datetimepicker",
#                   "label": "預約",
#                   "data": json.dumps(data),
#                   "mode": "datetime"
#               }
#             ]
#         }
#     }
#     return message


# def getTodayCovid19Message():
#     response = requests.get(
#         "https://covid-19.nchc.org.tw/api/covid19?CK=covid-19@nchc.org.tw&querydata=3001&limited=BGD", headers=HEADER)
#     data = response.json()[0]
#     date = data['a04']
#     total_count = data['a05']
#     count = data['a06']
#     return F"日期：{date}, 人數：{count}, 確診總人數：{total_count}"


# @app.route('/upload_file', methods=['POST'])
# def upload_file():
#     payload = dict()
#     if request.method == 'POST':
#         file = request.files['file']
#         print("json:", request.json)
#         form = request.form
#         age = form['age']
#         gender = ("男" if form['gender'] == "M" else "女") + "性"
#         if file:
#             filename = file.filename
#             img_path = os.path.join(UPLOAD_FOLDER, filename)
#             file.save(img_path)
#             print(img_path)
#             payload["to"] = my_line_id
#             payload["messages"] = [getImageMessage(F"{end_point}/{img_path}"),
#                                    {
#                 "type": "text",
#                 "text": F"年紀：{age}\n性別：{gender}"
#             }
#             ]
#             pushMessage(payload)
#     return 'OK'


# @app.route('/line_login', methods=['GET'])
# def line_login():
#     if request.method == 'GET':
#         code = request.args.get("code", None)
#         state = request.args.get("state", None)

#         if code and state:
#             HEADERS = {'Content-Type': 'application/x-www-form-urlencoded'}
#             url = "https://api.line.me/oauth2/v2.1/token"
#             FormData = {"grant_type": 'authorization_code', "code": code, "redirect_uri": F"{end_point}/line_login",
#                         "client_id": line_login_id, "client_secret": line_login_secret}
#             data = parse.urlencode(FormData)
#             content = requests.post(url=url, headers=HEADERS, data=data).text
#             content = json.loads(content)
#             url = "https://api.line.me/v2/profile"
#             HEADERS = {
#                 'Authorization': content["token_type"]+" "+content["access_token"]}
#             content = requests.get(url=url, headers=HEADERS).text
#             content = json.loads(content)
#             name = content["displayName"]
#             userID = content["userId"]
#             pictureURL = content["pictureUrl"]
#             statusMessage = content["statusMessage"]
#             print(content)
#             return render_template('profile.html', name=name, pictureURL=pictureURL, userID=userID, statusMessage=statusMessage)
#         else:
#             return render_template('login.html', client_id=line_login_id,
#                                    end_point=end_point)
