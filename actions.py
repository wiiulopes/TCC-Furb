# ! /usr/bin/env python
# -*- coding: utf-8 -*-

# Autor: William Lopes
# Data: 14/08/2019
# Linguagem: Python

# ========= IMPORTANTE ===========
# # # O codigo esta livre para usar,
# # # citar e compartilhar desde que
# # # mantida sua fonte e seu autor.
# # # Obrigado.

# =========== Resumo =============
# Classe responsavel pelas ações
# do sistema

from database import conectDatabase
from tts import textToSpeech
import math
import sys
import pynmea2
import serial
import time
import py_qmc5883l

sensor = py_qmc5883l.QMC5883L()
ser = serial.Serial("/dev/ttyAMA0", 9600, timeout=0.5)

resultdistanciaDirecao = []


def setDirection(resultBearing):
    if resultBearing > 338 or resultBearing < 22:
        bearing = "a frente"
    elif resultBearing > 22 and resultBearing < 68:
        bearing = "a frente a direita"
    elif resultBearing > 68 and resultBearing < 113:
        bearing = "a direita"
    elif resultBearing > 113 and resultBearing < 158:
        bearing = "atrás a direita"
    elif resultBearing > 158 and resultBearing < 203:
        bearing = "atrás"
    elif resultBearing > 203 and resultBearing < 248:
        bearing = "atrás a esquerda"
    elif resultBearing > 248 and resultBearing < 293:
        bearing = "a esquerda"
    elif resultBearing > 293 and resultBearing < 338:
        bearing = "a frente a esquerda"
    return bearing

def buscaUltimaPosicao():
    cursor = conectDatabase().cursor()
    cursor.execute("SELECT * FROM posicao_atual ORDER BY id DESC LIMIT 1")
    resultado = cursor.fetchone()
    cursor.close()
    return resultado


def distanciaDirecao():
    global resultdistanciaDirecao
    currentPosition = gps()
    currentBearing = compass()
    resut = []
    br = textToSpeech()
    cursor = conectDatabase().cursor()
    sql = ("SELECT *, (6371 * acos(cos(radians('%s')) * cos(radians(lat)) * cos(radians('%s')- radians(lng)) + "
           "sin(radians('%s')) * sin(radians(lat))))AS distance FROM coordenada HAVING distance <= '%s'")

    try:
        cursor.execute(sql, (currentPosition[0], currentPosition[1], currentPosition[0], 0.2))
        result = cursor.fetchall()
        # print("resultado "+result)
        for data in result:
            lat = float(data[1])
            lng = float(data[2])
            pointInterest = data[3]
            distanceMeters = str(int(round(data[4], 4) * 1000))
            destinationPosition = lat, lng
            finishBearingPosition = calculate_initial_compass_bearing(currentPosition, destinationPosition)
            if currentBearing < finishBearingPosition:
                resultBearing = finishBearingPosition - currentBearing
            else:
                auxBearing = currentBearing - finishBearingPosition
                resultBearing = 360 - auxBearing

            bearing = setDirection(resultBearing)
            print(pointInterest + " a " + distanceMeters + " metros " + bearing)
            resultdistanciaDirecao.append(pointInterest + " a " + distanceMeters + " metros " + bearing)
            # br.say(pointInterest + " a " + distanceMeters + " metros " + bearing)
            #br.runAndWait()

    except:
        br.say("Nenhum ponto de interesse por perto")
        br.runAndWait()

    return resultdistanciaDirecao

def compass():
    sensor.declination = -19.31
    bearing = sensor.get_bearing()
    return bearing


def gps():
    while True:
        data = ser.readline()
        if sys.version_info[0] == 3:
            data = data.decode("utf-8", "ignore")
        if data[0:6] == '$GNGGA':
            newmsg = pynmea2.parse(data)
            lat = round(newmsg.latitude, 6)
            lng = round(newmsg.longitude, 6)
            break;

    return lat, lng


def calculate_initial_compass_bearing(pointA, pointB):
    startx, starty, endx, endy = pointA[0], pointA[1], pointB[0], pointB[1]
    angle = math.atan2(endy - starty, endx - startx)
    if angle >= 0:
        return math.degrees(angle)
    else:
        return math.degrees((angle + 2 * math.pi))


if __name__ == "__main__":
    distanciaDirecao()
