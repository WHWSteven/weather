from __future__ import unicode_literals
from urllib import parse
import string
from flask import Flask, request, abort, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, MessageTemplateAction, FlexSendMessage, BubbleContainer, ImageComponent
from linebot.models import PostbackAction, URIAction, MessageAction, TemplateSendMessage, ButtonsTemplate, CarouselTemplate,  CarouselColumn
from linebot.models import *
import requests
import json
import configparser
import os
import time
import logging
import openai
# 1.setup log path and create log directory
logName = 'MyProgram.log'
logDir = 'log'
logPath = logDir + '/' + logName


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


key_city = ['基隆市天氣', '嘉義市天氣', '臺北市天氣', '台北市天氣', '嘉義縣天氣', '新北市天氣', '臺南市天氣', '台南市天氣', '桃園市天氣', '高雄市天氣', '新竹市天氣', '屏東縣天氣', '桃園縣天氣',
            '宜蘭市天氣', '新竹縣天氣', '臺東縣天氣', '台東縣天氣', '苗栗縣天氣', '花蓮縣天氣', '臺中市天氣', '台中市天氣', '宜蘭縣天氣', '彰化縣天氣', '澎湖縣天氣', '南投縣天氣', '金門縣天氣', '雲林縣天氣', '連江縣天氣']


@ app.route("/", methods=['POST', 'GET'])
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

                if text == "各縣市天氣查詢":
                    payload["messages"] = [flx()]
                elif text == "天氣查詢":
                    payload["messages"] = [
                        reply_weather_table(), reply_weather_table2()]
                elif text == "t":
                    payload["messages"] = [t()]
                elif text in {'雷達', '雷達回波'}:
                    line_bot_api.reply_message(
                        replyToken, ImageSendMessage(original_content_url=f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}',
                                                     preview_image_url=f'https://cwbopendata.s3.ap-northeast-1.amazonaws.com/MSC/O-A0058-003.png?{time.time_ns()}'
                                                     ))

                elif text == '地震' or text == '地震查詢':
                    u = get_eq_pic()
                    line_bot_api.reply_message(
                        replyToken, ImageSendMessage(original_content_url=u,
                                                     preview_image_url=u
                                                     ))

                elif text in key_city:
                    if text[0] == '台':
                        text = text.replace('台', '臺')
                    user_city = text[:3]
                    weather = getWeather(user_city)
                    wx = wxx(weather)
                    ci = ciw(weather)
                    msg_weaterInfo = transferWeatherData(weather)
                    # msg_weaterInfo[3] = 80
                    # msg_weaterInfo[8] = 100
                    if msg_weaterInfo[3] > 42:
                        url = 'https://cdn-icons-png.flaticon.com/512/622/622085.png'
                    elif 41 > msg_weaterInfo[3] & msg_weaterInfo[3] > 20:
                        url = 'https://cdn-icons-png.flaticon.com/512/2042/2042088.png'
                    else:
                        url = 'https://cdn-icons-png.flaticon.com/512/1838/1838873.png'
                    if msg_weaterInfo[8] > 42:
                        url1 = 'https://cdn-icons-png.flaticon.com/512/622/622085.png'
                    else:
                        url1 = 'https://cdn-icons-png.flaticon.com/512/1838/1838873.png'

                    line_bot_api.reply_message(
                        replyToken, TemplateSendMessage(
                            alt_text=user_city + '未來 36 小時天氣預測',
                            template=CarouselTemplate(
                                columns=[
                                    CarouselColumn(
                                        thumbnail_image_url=url,
                                        title='{}'.format(
                                            msg_weaterInfo[0]),
                                        text='天氣狀況： \t{}\n舒適度： \t{}\n溫度： \t{}°C  至 \t{}°C \n降雨機率： {}%\n\n{}\n{}\n{}'.format(
                                            wx[0], ci[0], msg_weaterInfo[
                                                1], msg_weaterInfo[2], msg_weaterInfo[3], msg_weaterInfo[9], msg_weaterInfo[10], msg_weaterInfo[11]
                                        ),
                                        actions=[
                                            URIAction(
                                                label='氣象局詳細內容',
                                                uri='https://www.cwb.gov.tw/V8/C/W/County/index.html'
                                            )
                                        ]
                                    ),
                                    CarouselColumn(
                                        thumbnail_image_url=url1,
                                        title='{}'.format(
                                            msg_weaterInfo[5]),
                                        text='天氣狀況： \t{}\n舒適度： \t{}\n溫度： \t{}°C  至 \t{}°C \n降雨機率： {}%\n'.format(
                                            wx[2], ci[2],  msg_weaterInfo[6], msg_weaterInfo[7], msg_weaterInfo[8]),

                                        actions=[
                                            URIAction(
                                                label='氣象局詳細內容',
                                                uri='https://www.cwb.gov.tw/V8/C/W/County/index.html'
                                            )
                                        ]
                                    )

                                ]
                            )


                        ))

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
                # payload["messages"] = [
                #     getLocationConfirmMessage(title, latitude, longitude)]
                logger.info(payload)
                replyMessage(payload)

            else:
                data = json.loads(events[0]["postback"]["data"])
                logger.info(data)
                action = data["action"]
                # if action == "get_near":
                #     data["action"] = "get_detail"
                #     payload["messages"] = [getCarouselMessage(data)]
                # elif action == "get_detail":
                #     del data["action"]
                #     payload["messages"] = [getTaipei101ImageMessage(),
                #                            getTaipei101LocationMessage(),
                #                            getMRTVideoMessage(),
                #                            getCallCarMessage(data)]
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


def get_eq_pic():
    msg = ['找不到地震資訊']            # 預設回傳的訊息
    try:
        code = 'CWB-5903F8B2-FC6A-4703-9440-01FDFD7B64B2'
        url = f'https://opendata.cwb.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={code}'
        e_data = requests.get(url)                                   # 爬取地震資訊網址
        eq = (json.loads(e_data.text)
              )['records']['Earthquake']
        for i in eq:
            img = i['ReportImageURI']                                # 地震圖
            msg = img
            break     # 取出第一筆資料後就 break
        return msg    # 回傳 msg
    except:
        return msg    # 如果取資料有發生錯誤，直接回傳 msg


def reply_weather_table():
    with open("./json/weather_table.json", 'r', encoding='utf-8') as f:
        message = json.load(f)
    return message


def reply_weather_table2():
    with open("./json/weather_table2.json", 'r', encoding='utf-8') as f:
        message = json.load(f)
    return message


def t():
    with open("./json/t.json", 'r', encoding='utf-8') as f:
        message = json.load(f)
    return message


def flx():
    line_bot_api.push_message(my_line_id, FlexSendMessage(
        alt_text='各縣市天氣查詢',
        contents={

            "type": "carousel",
            "contents": [
                {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "請選擇想查詢的縣市",
                                "weight": "bold",
                                "size": "md",
                                "decoration": "none",
                                "align": "center",
                                "gravity": "top"
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [],
                                "spacing": "xs",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "text": "基隆市天氣",
                                            "label": "基隆市"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"

                                    },

                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "宜蘭縣",
                                            "text": "宜蘭縣天氣"

                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary", "position": "relative",
                                        "margin": "sm"

                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "臺北市",
                                            "text": "臺北市天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "新北市",
                                            "text": "新北市天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "桃園市",
                                            "text": "桃園市天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "桃園縣",
                                            "text": "桃園縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "新竹市",
                                            "text": "新竹市天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "新竹縣",
                                            "text": "新竹縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "苗栗縣",
                                            "text": "苗栗縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "臺中市",
                                            "text": "臺中市天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "彰化縣",
                                            "text": "彰化縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "南投縣",
                                            "text": "南投縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "雲林縣",
                                            "text": "雲林縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "嘉義市",
                                            "text": "嘉義市天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "嘉義縣",
                                            "text": "嘉義縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "臺南市",
                                            "text": "臺南市天氣",

                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "高雄市",
                                            "text": "高雄市天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "屏東縣",
                                            "text": "屏東縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            }
                        ],

                        # "background": {
                        #     "color": "#ffedbc"

                        #     #     "type": "linearGradient",
                        #     #     "angle": "0deg",
                        #     #     "endColor": "#89cff0",
                        #     #     "startColor": "#fffeec"
                        # }
                    },
                    "footer": {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "margin": "none",
                                "height": "sm",
                                "style": "link",
                                "color": "#6d6c6c",
                                "gravity": "bottom",
                                "action":  {
                                    "type": "uri",
                                    "label": "資料來源：中央氣象局",
                                    "uri": "https://www.cwb.gov.tw/V8/C/"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "請選擇想查詢的縣市",
                                "weight": "bold",
                                "size": "md",
                                "decoration": "none",
                                "align": "center",
                                "gravity": "top"
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [],
                                "spacing": "xs",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "text": "花蓮縣天氣",
                                            "label": "花蓮縣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"

                                    },

                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "臺東縣",
                                            "text": "臺東縣天氣"

                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary", "position": "relative",
                                        "margin": "sm"

                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },

                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "澎湖縣",
                                            "text": "澎湖縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    },
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "金門縣",
                                            "text": "金門縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "message",
                                            "label": "連江縣",
                                            "text": "連江縣天氣"
                                        },
                                        "color": "#d3d3d3",
                                        "style": "secondary",
                                        "position": "relative",
                                        "margin": "sm"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            },

                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "separator",
                                        "margin": "sm",
                                        "color": "#ffffff"
                                    }
                                ]
                            }

                        ],

                        # "background": {
                        #     "color": "#87cefa"

                        #     #     "type": "linearGradient",
                        #     #     "angle": "0deg",
                        #     #     "endColor": "#89cff0",
                        #     #     "startColor": "#fffeec"
                        # }
                    },
                    "footer": {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "margin": "none",
                                "height": "sm",
                                "style": "link",
                                "color": "#6d6c6c",
                                "gravity": "bottom",
                                "action":  {
                                    "type": "uri",
                                    "label": "資料來源：中央氣象局",
                                    "uri": "https://www.cwb.gov.tw/V8/C/"
                                }
                            }
                        ]
                    }
                }
            ]
        }

    ))


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


def wxx(item):
    # 天氣現象
    cityName = item["locationName"]
    weatherElement = item["weatherElement"]
    if (weatherElement[0]["elementName"] == 'Wx'):
        timeDicts = weatherElement[0]["time"]  # 依時間區段設定早晚跟明天
        Wx_morning = timeDicts[0]["parameter"]["parameterName"]
        Wx_night = timeDicts[1]["parameter"]["parameterName"]
        Wx_tomorrow = timeDicts[2]["parameter"]["parameterName"]
    wx = {}
    wx[0] = Wx_morning
    wx[1] = Wx_night
    wx[2] = Wx_tomorrow
    return wx


def ciw(item):
    cityName = item["locationName"]
    weatherElement = item["weatherElement"]

# 舒適度
    if (weatherElement[3]["elementName"] == 'CI'):
        timeDicts = weatherElement[3]["time"]  # 依時間區段設定早晚跟明天
        CI_morning = timeDicts[0]["parameter"]["parameterName"]
        CI_night = timeDicts[1]["parameter"]["parameterName"]
        CI_tomorrow = timeDicts[2]["parameter"]["parameterName"]
    ci = {}
    ci[0] = CI_morning
    ci[1] = CI_night
    ci[2] = CI_tomorrow
    return ci


def transferWeatherData(item):
    cityName = item["locationName"]
    weatherElement = item["weatherElement"]  # 取得該縣市的天氣資料

# 降雨機率
    if (weatherElement[1]["elementName"] == 'PoP'):
        timeDicts = weatherElement[1]["time"]  # 依時間區段設定早晚跟明天
        PoP_morning = int(timeDicts[0]["parameter"]["parameterName"])
        PoP_night = int(timeDicts[1]["parameter"]["parameterName"])
        PoP_tomorrow = int(timeDicts[2]["parameter"]["parameterName"])

# 低溫
    if (weatherElement[2]["elementName"] == 'MinT'):
        timeDicts = weatherElement[2]["time"]
        # 依時間區段設定早晚跟明天
        MinT_morning = timeDicts[0]["parameter"]["parameterName"]
        MinT_night = timeDicts[1]["parameter"]["parameterName"]
        MinT_tomorrow = timeDicts[2]["parameter"]["parameterName"]

# 高溫
    if (weatherElement[4]["elementName"] == 'MaxT'):
        timeDicts = weatherElement[4]["time"]  # 依時間區段設定早晚跟明天
        MaxT_morning = timeDicts[0]["parameter"]["parameterName"]
        MaxT_night = timeDicts[1]["parameter"]["parameterName"]
        MaxT_tomorrow = timeDicts[2]["parameter"]["parameterName"]

        today = timeDicts[0]["startTime"].split(
            ",")
        tomorrow = timeDicts[2]["endTime"].split(
            ",")
    if MaxT_morning > MaxT_night:
        max_t = MaxT_morning
    elif MaxT_morning < MaxT_night:
        max_t = MaxT_night
    else:
        max_t = MaxT_morning
    if MinT_morning < MinT_night:
        min_t = MinT_morning
    elif MinT_morning > MinT_night:
        min_t = MinT_night
    else:
        min_t = MinT_night

    replyMsg = {}
    replyMsg[0] = str(today[0][0:10])
    replyMsg[1] = min_t
    replyMsg[2] = max_t
    replyMsg[3] = PoP_morning
    replyMsg[4] = PoP_night
    replyMsg[5] = str(tomorrow[0][0:10])
    replyMsg[6] = MinT_tomorrow
    replyMsg[7] = MaxT_tomorrow
    replyMsg[8] = PoP_tomorrow
    replyMsg[9] = ""
    replyMsg[10] = ""
    replyMsg[11] = ""

    # replyMsg =  \
    #     str(today[0][0:10]) + min_t + max_t + PoP_morning + PoP_night + \
    #     str(tomorrow[0][0:10]) + \
    #     MinT_tomorrow + MaxT_tomorrow + PoP_tomorrow


# 低溫提醒
# notice_minT()
    minT = min([weatherElement[2]["time"][0]["parameter"]["parameterName"], weatherElement[2]["time"]
                [1]["parameter"]["parameterName"], weatherElement[2]["time"][2]["parameter"]["parameterName"]])
# 高溫提醒
    maxT = max([weatherElement[4]["time"][0]["parameter"]["parameterName"], weatherElement[4]["time"]
                [1]["parameter"]["parameterName"], weatherElement[4]["time"][2]["parameter"]["parameterName"]])
    pop = max([weatherElement[1]["time"][0]["parameter"]["parameterName"], weatherElement[1]["time"]
               [1]["parameter"]["parameterName"], weatherElement[1]["time"][2]["parameter"]["parameterName"]])

    if (int(min_t) < 13):
        replyMsg[9] = "請注意低溫\n"
        return (replyMsg)

    elif (int(max_t) > 36):
        replyMsg[10] = "請注意高溫\n"
        return (replyMsg)

    elif (int(pop) > 42):  # 降雨提醒 pop=12h/ pop6=6h
        replyMsg[11] = "請攜待雨具\n"
        return (replyMsg)

    else:
        return replyMsg


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
