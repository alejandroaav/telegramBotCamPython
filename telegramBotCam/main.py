from datetime import datetime
import time
import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove
import cv2
import requests
from requests.exceptions import HTTPError
import numpy as np
import math
import imutils
import os
import subprocess
from ultralytics import YOLO
from google.cloud import storage
from dotenv import load_dotenv
from requests.exceptions import ConnectionError
load_dotenv()

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
chat_id = os.getenv('CHAT_ID')
ipCam = os.getenv('IP_CAMERA')
videoDuracion=10 # duracion aprox. del video capturado
tiempoEntreImagenVigiliaPasiva=5
tiempoEntreImagenVigiliaActiva=3
gcpBucketImagenes=True # envia la imagen detectada en vigilancia a cloud storage
detectionConfidence=0.7
videoFps=10
objectToDetect = ['person'] #car, cat, dog, person
maxConnectionReintent = 5
vigiliaReintent=0
imgW=800
imgH=600

#markup = types.InlineKeyboardMarkup(row_width=2)  # row_width: number of buttons
#markup.add(
#    types.InlineKeyboardButton("Foto", callback_data="foto")
#    ,types.InlineKeyboardButton("Video", callback_data="video")
#    ,types.InlineKeyboardButton("Start", callback_data="start")
#    ,types.InlineKeyboardButton("Stop", callback_data="stop")
#)

now_init = datetime.now()
dt_init = now_init.strftime("%Y%m%d_%H:%M:%S")
msgTxt = "@@@ \N{rocket} {} - Bot vigía iniciado @@@".format(dt_init)
msgTxt = msgTxt + "\ningrese: /foto para tomar una foto"
msgTxt = msgTxt + "\ningrese: /video para obtener un video de 10seg"
msgTxt = msgTxt + "\ningrese: /agrega para agregar perros, gatos, automoviles, etc. a vigilar"
msgTxt = msgTxt + "\ningrese: /start para iniciar la vigilia"
msgTxt = msgTxt + "\ningrese: /stop para finalizar la vigilia"
#msgTxt = msgTxt + "\ningrese: /TEST para la prueba"
msgTxt = msgTxt + "\nQue desea realizar ?"

#bot.send_message(chat_id, msgTxt, reply_markup=markup)
bot.send_message(chat_id, msgTxt)

# model
model = YOLO("yolo-Weights/yolov8n.pt")

# object classes
classNames = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
              'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse',
              'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
              'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
              'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon',
              'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut',
              'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
              'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book',
              'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "foto":
        bot.answer_callback_query(call.id, "Tomando foto...")
        foto(call)
    if call.data == "video":
        bot.answer_callback_query(call.id, "Grabando video...")
        video(call)
    global sw
    if call.data == "start":
        start(call)
    if call.data == "stop":
        stop(call)
    if call.data == "agrega":
        agrega(call)

def camCvImg():
    try:
        cap = cv2.VideoCapture(0)
        if (cap.isOpened() == False):
            print("Error reading video source")
            return
        #key = cv2.waitKey(1)
        check, frame = cap.read()
        cap.release()
        return frame
    except Exception as err:
        print(f'Ha ocurrido un error: {err}')  # Python 3.6
        bot.send_message(chat_id, "Un error ha ocurrido")


@bot.message_handler(commands=['foto'])
def foto(message):
    try:
        print("Tomando foto…")
        bot.send_message(chat_id, 'Tomando foto...')
        img = camCvImg()
        img = imutils.resize(img, width=imgW, height=imgH)
        # Convertir image to byte
        img_byte = cv2.imencode('.png', img)[1]
        bot.send_photo(chat_id, photo=img_byte)
        bot.send_message(chat_id, '\N{camera} /foto')
    except HTTPError as http_err:
        print(f'HTTP ha ocurrido un error: {http_err}')  # Python 3.6
        bot.send_message(chat_id, "No se pudo conectar con la Cámara")
    except Exception as err:
        print(f'Ha ocurrido un error: {err}')  # Python 3.6
        bot.send_message(chat_id, "Un error ha ocurrido")

@bot.message_handler(commands=['video'])
def video(message):
    try:
        cap = cv2.VideoCapture(0)
        if (cap.isOpened() == False):
            print("Error reading video source")
            return
    except HTTPError as http_err:
        print(f'HTTP ha ocurrido un error: {http_err}')
        bot.send_message(chat_id, "No se pudo conectar con la Cámara")
    except ConnectionError as connErr:
        print(f'Ha ocurrido un error: {connErr}')
        bot.send_message(chat_id, "Un error ha ocurrido al intentar conectar con la camara. No se ha podido obtener el video")
    except Exception as err:
        print(f'Ha ocurrido un error: {err}')
        bot.send_message(chat_id, "Un error ha ocurrido")
    else:
        bot.send_message(chat_id, 'Capturando video...')
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H:%M:%S_")
        video_name = dt_string + 'video.mp4'

        img_array = []
        t0 = time.time()
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        print(f'Capturando video… {video_name} - H{frame_height}|W{frame_width}')
        size = (frame_width, frame_height)
        grabador = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), 10, size)
        while True:
            ret, frame = cap.read()
            #cv2.imshow('frame', frame)
            grabador.write(frame)

            if time.time() - t0 > videoDuracion + 2:
                #grabador = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'mp4v'), 10, size)
                break

        for i in range(len(img_array)):
            grabador.write(img_array[i])

        cap.release()
        grabador.release()
        cv2.destroyAllWindows()
        print("{} written!".format(video_name))

        video = open(video_name, 'rb')
        bot.send_video(chat_id, video, timeout=videoDuracion + 5)
        bot.send_message(chat_id, '\N{movie camera} /video')
        os.remove(video_name)

@bot.message_handler(commands=['agrega'])
def agrega(message):
    markup1 = types.ReplyKeyboardMarkup(row_width=3)
    # Add to buttons by list with ours generate_buttons function.
    markup1 = generate_buttons(['person', 'dog', 'cat', 'car'], markup1)
    message = bot.reply_to(message, """Que desea agregar a la vigilia?""", reply_markup=markup1)
    bot.register_next_step_handler(message, addToVigilia)


@bot.message_handler(commands=['start'])
def start(message):
    global sw
    sw = True
    vigila()


@bot.message_handler(commands=['stop'])
def stop(message):
    print('STOP VIGILIA')
    global sw
    sw = False

def vigila():
    try:
        if sw:
            timeWait = tiempoEntreImagenVigiliaPasiva
            bot.send_message(chat_id, 'VIGILIA INICIADA...\N{eyes}')
            while sw:
                img = camCvImg()
                # img = imutils.resize(img, width=480, height=640)

                results = model(img, stream=True, conf=detectionConfidence, classes=[0, 1, 2, 14, 15, 16, 17, 18, 19])
                cantRes = 0
                for r in results:  # cantidad de detecciones
                    boxes = r.boxes
                    for box in boxes:
                        # confidence
                        confidence = math.ceil((box.conf[0] * 100)) / 100
                        # class name
                        cls = int(box.cls[0])

                        if (confidence >= detectionConfidence and (classNames[cls] in objectToDetect)):

                            subprocess.run('spd-say -t female3 -l es "Atención, Persona detectada"', shell=True, check=True, capture_output=False, encoding='utf-8')
                            # bounding box
                            cantRes += 1
                            x1, y1, x2, y2 = box.xyxy[0]
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # convert to int values

                            # put box in cam
                            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)

                            # print("Confidence --->", confidence)
                            # print("Class name -->", classNames[cls])

                            # object details
                            org = [x1 + 20, y1 + 30]
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            fontScale = 0.75
                            color = (255, 0, 0)
                            thickness = 2
                            cv2.putText(img, classNames[cls] + " - " + str(confidence), org, font, fontScale, color,
                                        thickness)

                            now = datetime.now()
                            dt = now.strftime("%Y%m%d_%H:%M:%S")
                            img_name = "DETECTION_opencv_frame_{}.png".format(dt)
                            imgChat = imutils.resize(img, width=640, height=480)

                            img_byte_chat = cv2.imencode('.png', imgChat)[1]
                            bot.send_photo(chat_id, photo=img_byte_chat)

                            bot.send_message(chat_id, '\N{shield} DETECCION !! /stop ?')
                            timeWait = tiempoEntreImagenVigiliaActiva
                            if gcpBucketImagenes:
                                img_byte = cv2.imencode('.png', img)[1].tobytes()
                                upload_file(img_name, img_byte)
                                bot.send_message(chat_id, img_name)
                        else:
                            timeWait = tiempoEntreImagenVigiliaPasiva

                time.sleep(timeWait)

        bot.send_message(chat_id, '\N{raised hand} VIGILIA FINALIZADA...')
    except HTTPError as http_err:
        print(f'HTTP ha ocurrido un error: {http_err}')
        bot.send_message(chat_id, "No se pudo conectar con la Cámara")
    except Exception as err:
        print(f'Ha ocurrido un error: {err}')
        bot.send_message(chat_id, "Un error ha ocurrido")



def upload_file(file_name,bytes):
    try:
        # Obtener un cliente de Cloud Storage
        storage_client = storage.Client()

        # Obtener la referencia al depósito
        bucket_name = "files-security-cam"
        bucket = storage_client.bucket(bucket_name)

        # Obtener la referencia al objeto
        object = bucket.blob(file_name)

        # Subir la imagen
        object.upload_from_string(bytes, content_type="image/png")

        print(f'Imagen enviada a la nube {object.public_url}')
        return True
    except Exception as err:
        print(f"Algo salio mal al intentar subir el archivo al Bucket {err}")
        return False

@bot.message_handler(commands=['TEST'])
def get_photo_pc(call):
    print(f'Call from {call.from_user.first_name} - Chat ID:{call.chat.id}, User Id: {call.from_user.id}, Message Id: {call.message_id}')
    try:
        # Capturar la cámara
        cap = cv2.VideoCapture(0)

        # Tomar un marco
        ret, frame = cap.read()

        img = imutils.resize(frame, width=imgW, height=imgH)
        img_byte = cv2.imencode('.png', img)[1]
        bot.send_photo(chat_id, photo=img_byte)

        # Cerrar la cámara
        cap.release()
    except Exception as err:
        print(f"un error ha ocurrido: {err}")


def addToVigilia(message):
    name = message.text
    exist = False
    for obj in objectToDetect:
        if (name == obj):
            exist = True

    if (exist):
        objectToDetect.remove(name)
    else:
        objectToDetect.append(name)
    print(objectToDetect)
    msgTxt = f'En vigilia: {objectToDetect}'
    msgTxt = msgTxt + '\n/start para comenzar la vigilia'
    bot.send_message(chat_id, msgTxt, reply_markup=ReplyKeyboardRemove())

#This will generate buttons for us in more elegant way
def generate_buttons(bts_names, markup):
    for button in bts_names:
        markup.add(types.KeyboardButton(button))
    return markup


sw = True
#cv2.namedWindow("test")
print('Bot iniciado ')
bot.infinity_polling()
now_init = datetime.now()
dt_fin = now_init.strftime("%Y%m%d_%H:%M:%S")
msgTxt = f'@@@ \N{no entry} {dt_fin} - Bot Finalizado !! @@@'
bot.send_message(chat_id, msgTxt)
print('Bot finalizando !!')
cv2.destroyAllWindows()
