from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
import RPi.GPIO as IO
IO.setmode(IO.BCM)
from RPLCD.i2c import CharLCD
import time
from threading import Thread
from pyparticleio.ParticleCloud import ParticleCloud
from PyQt5 import QtCore

# Global variables
global lcd_message
lcd_message = ""
global new_message
new_message = False
global detected
detected = False
global openParcel
openParcel = False
global LedOn
LedOn = False
global visitorButton
visitorButton = False
global deliveryButton
deliveryButton = False
global Guest
Guest = "---"
global GuestResponse
GuestResponse = "---"

global Temperature
Temperature = 0.0
global Humidity
Humidity = 0.0
global Humidifier_status
Humidifier_status= "OFF"
global AirCon_status 
AirCon_status= "OFF"

access_token = "d8e40e36385b7b1e4f51211addd2c1e968f0ff90"
device_id = "e00fce68b680c7677dc6eb72"
global particle_cloud
particle_cloud = ParticleCloud(username_or_access_token=access_token, device_ids = device_id)

class lcd:
    def __init__(self):
        self.__running = True
        self.lcd = CharLCD('PCF8574', 0x27)
        self.lcd.clear()
        self.visitor_BUTTON_PIN = 6
        self.delivery_BUTTON_PIN = 13
        self.yes_BUTTON_PIN = 19
        self.no_BUTTON_PIN = 26
        
        # Setup buttons
        IO.setup(self.visitor_BUTTON_PIN, IO.IN, pull_up_down=IO.PUD_UP)
        IO.setup(self.delivery_BUTTON_PIN, IO.IN, pull_up_down=IO.PUD_UP)
        IO.setup(self.yes_BUTTON_PIN, IO.IN, pull_up_down=IO.PUD_UP)
        IO.setup(self.no_BUTTON_PIN, IO.IN, pull_up_down=IO.PUD_UP)
    
    def GuestMessage(self, message):
        global new_message
        global lcd_message
        new_message = True
        lcd_message = message
        
    def run(self):
        global lcd_message
        global new_message
        global visitorButton
        global deliveryButton
        global Guest
        global GuestResponse
        global openParcel
        
        while self.__running:
            if new_message:
                self.lcd.clear()
                self.lcd.write_string(lcd_message)
                new_message = False
                time.sleep(1)
            
            if IO.input(self.visitor_BUTTON_PIN) == False:
                Guest = "Visitor"
                visitorButton = True
                deliveryButton = False
                self.GuestMessage("Hi Visitor! Justin is notified! Please wait for Justin's response.")
                time.sleep(0.5)
                
            if IO.input(self.delivery_BUTTON_PIN) == False:
                Guest = "Delivery"
                visitorButton = False
                deliveryButton = True
                self.GuestMessage("Hi There, Please leave packages in the parcel box! Thank You")
                time.sleep(2)
                openParcel = True
                time.sleep(0.5)
                
            if IO.input(self.yes_BUTTON_PIN) == False:
                GuestResponse = "YES"
                time.sleep(0.5)
                
            if IO.input(self.no_BUTTON_PIN) == False:
                GuestResponse = "NO"
                time.sleep(0.5)
                
    def terminate(self):
        self.__running = False

class ControlDevices:
    def __init__(self):
        self.__running = True
        # Pins
        self.SERVO_PIN = 4
        self.ECHO = 24
        self.TRIG = 23
        self.LED_PIN = 5
        # control variables
        self.closeDutyPWM = 5
        self.openDutyPWM = 10
        self.openParcelDuration = 5
        
        self.setup()
        
    def setup(self):
        # Setup Servo Motor         
        IO.setup(self.SERVO_PIN, IO.OUT)
        self.servo = IO.PWM(self.SERVO_PIN, 50)
        self.servo.start(self.closeDutyPWM)
        # Setup Ultra sonic sensor
        IO.setup(self.TRIG, IO.OUT)
        IO.setup(self.ECHO, IO.IN)
        # Setup LED light
        IO.setup(self.LED_PIN, IO.OUT)
        
        
    def terminate(self):  
        self.__running = False
        
    def GuestMessage(self, message):
        global new_message
        global lcd_message
        new_message = True
        lcd_message = message
        
    def Distance(self):
        IO.output(self.TRIG, True)
        time.sleep(0.00001)
        IO.output(self.TRIG, False)
        
        startTime = time.time()
        stopTime = time.time()
        
        while IO.input(self.ECHO) == 0:
            startTime = time.time()
        
        while IO.input(self.ECHO) == 1:
            stopTime = time.time()
            
        timeElapsed = stopTime - startTime
        distance = timeElapsed*34300/2
        
        return distance

    def run(self):
        global openParcel
        global detected
        global Guest
        global LedOn
        
        while self.__running:
            # Detect motion
            d = self.Distance()
            print(d)
            if d <= 10:
                if detected == False:
                    self.GuestMessage("Hi There, Welcome to Justin house! Please press buttons.")
                detected = True
#             else:
#                 detected = False
#                 Guest = "---"
                    
            # Listening for Parcel box controlling
            if openParcel:
                openParcel = False
                self.GuestMessage("Parcel Box is opened Closing in " + str(self.openParcelDuration) + " seconds")
                time.sleep(1)
                self.servo.ChangeDutyCycle(self.openDutyPWM)
                time.sleep(self.openParcelDuration)
                self.servo.ChangeDutyCycle(self.closeDutyPWM)
                time.sleep(1)

            # Listening for led controlling
            if LedOn:
                IO.output(self.LED_PIN, IO.HIGH)
            else:
                IO.output(self.LED_PIN, IO.LOW)
                
            time.sleep(1)
            
class ArgonConnection:
    def __init__(self):
        self._running = True

    def terminate(self):  
        self._running = False  

    def run(self):
        global visitorButton
        global deliveryButton
        global Temperature
        global Humidity
        global Humidifier_status
        global AirCon_status
        
        while self._running:
            # Get data from room sensors
            try:
                Temperature = round(particle_cloud.JustinArgon01.Temperature, 1)
                Humidity = round(particle_cloud.JustinArgon01.Humidity, 1)
                AirConditioner = particle_cloud.JustinArgon01.AirConditioner
                Humidifier = particle_cloud.JustinArgon01.Humidifier            
                
                print("Temp: {}, Hum: {}, AirCon: {}, Humidifier: {} ".format(Temperature, Humidity, Humidifier, AirConditioner))
                # Get Humidifier Status
                if (Humidifier == 1):
                    Humidifier_status = "ON"
                elif(Humidifier == 0):
                    Humidifier_status = "OFF"
                
                # Get Air Conditioner Status
                if (AirConditioner == -1):
                    AirCon_status = "COOLING"
                elif (AirConditioner == 0):
                    AirCon_status = "OFF"
                elif (AirConditioner == 1):
                    AirCon_status = "HEATING"
                
                if visitorButton == True and deliveryButton == False:
                    particle_cloud.JustinArgon01.publish("Guess_Notifications", "visitor")
                    # Reset state after pulished event
                    visitorButton = False
                    deliveryButton = False
                elif visitorButton == False and deliveryButton == True:
                    particle_cloud.JustinArgon01.publish("Guess_Notifications", "delivery")
                    # Reset state after pulished event
                    visitorButton = False
                    deliveryButton = False
                
                time.sleep(2)
            except:
                time.sleep(2)
            
            
class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("applayout.ui", self)
        
        # Find camera preview
        self.cameraPreview = self.findChild(QGraphicsView, 'graphicsViewCamera')
        # Find message box
        self.message = self.findChild(QLineEdit, 'lineEditUserMessage')
        # Find message box
        self.status = self.findChild(QLabel, 'textboxDoorStatus')
        # Find Temperature range spinbox
        self.maxTemp = self.findChild(QSpinBox, 'spinBoxMaxTemperature')
        self.minTemp = self.findChild(QSpinBox, 'spinBoxMinTemperature')
        # Find buttons
        self.buttonSendMessage = self.findChild(QPushButton, 'pushButtonUserSendMessage')
        self.buttonSendMessage.clicked.connect(self.displayMessageOnClicked)    
        self.buttonStart = self.findChild(QPushButton, 'pushButtonStart')
        self.buttonStart.clicked.connect(self.StartOnClicked)
        self.buttonOpenParcel = self.findChild(QPushButton, 'pushButtonOpenParcel')
        self.buttonOpenParcel.clicked.connect(self.openParcelOnClicked)
        # Find message box
        self.tempDisplay = self.findChild(QLCDNumber, 'lcdnumberTemperature')
        self.humDisplay = self.findChild(QLCDNumber, 'lcdnumberHumidity')
        # Find labels
        self.lightStatus = self.findChild(QLabel, 'labelLightStatus')
        self.motionStatus = self.findChild(QLabel, 'labelMotionStatus')
        self.guestStatus = self.findChild(QLabel, 'labelGuessStatus')
        self.guessReply = self.findChild(QLabel, 'labelReply')
        self.airConStatus = self.findChild(QLabel, 'labelAirConStatus')
        self.humidifierStatus = self.findChild(QLabel, 'labelHumidifierSatus')
        
        # Find RadioButtons
        # Door Light buttons        
        self.rbDoorLightOn = self.findChild(QRadioButton, 'radioButtonLedOn')
        self.rbDoorLightOff = self.findChild(QRadioButton, 'radioButtonLedOff')
        self.rbDoorLightOff.setChecked(True)
        self.rbDoorLightOn.toggled.connect(lambda:self.doorLightOnClicked(self.rbDoorLightOn))
        self.rbDoorLightOff.toggled.connect(lambda:self.doorLightOnClicked(self.rbDoorLightOff))
        # Air-Con Light buttons 
        self.rbAcHeat = self.findChild(QRadioButton, 'radioButtonACHeat')
        self.rbAcCool = self.findChild(QRadioButton, 'radioButtonACCool')
        self.rbAcOff = self.findChild(QRadioButton, 'radioButtonACOff')
        self.rbAcOff.setChecked(True)
        self.rbAcHeat.toggled.connect(lambda:self.airConOnClicked(self.rbAcHeat))
        self.rbAcCool.toggled.connect(lambda:self.airConOnClicked(self.rbAcCool))
        self.rbAcOff.toggled.connect(lambda:self.airConOnClicked(self.rbAcOff))
        # Humidifier buttons 
        self.rbHumidifierOn = self.findChild(QRadioButton, 'radioButtonHumidifierOn')
        self.rbHumidifierOff = self.findChild(QRadioButton, 'radioButtonHumidifierOff')
        self.rbHumidifierOff.setChecked(True)
        self.rbHumidifierOn.toggled.connect(lambda:self.humidifierOnClicked(self.rbHumidifierOn))
        self.rbHumidifierOff.toggled.connect(lambda:self.humidifierOnClicked(self.rbHumidifierOff))
        
        # Show window
        self.show()
    
    # Function: Door Light Controller    
    def doorLightOnClicked(self, rbDoorLight):
        global LedOn
        if rbDoorLight.isChecked():
            self.lightStatus.setText(rbDoorLight.text())
            if (rbDoorLight.text() == "ON"):
                LedOn = True
            else:
                LedOn = False
                
    # Function: Air Conditioner Controller    
    def airConOnClicked(self, rbAirCon):
        if rbAirCon.isChecked():
            if (rbAirCon.text() == "HEAT"):
                particle_cloud.JustinArgon01.publish("AirConditioner_Controller", "HEAT")
            elif (rbAirCon.text() == "COOL"):
                particle_cloud.JustinArgon01.publish("AirConditioner_Controller", "COOL")
            elif (rbAirCon.text() == "OFF"):
                particle_cloud.JustinArgon01.publish("AirConditioner_Controller", "OFF")
            
    # Function: Humidifier Controller    
    def humidifierOnClicked(self, rbHumidifier):
        if rbHumidifier.isChecked():
            if (rbHumidifier.text() == "ON"):
                particle_cloud.JustinArgon01.publish("Humidifier_Controller", "ON")
            elif (rbHumidifier.text() == "OFF"):
                particle_cloud.JustinArgon01.publish("Humidifier_Controller", "OFF")
    
    def displayMessageOnClicked(self):
        global new_message
        global lcd_message
        new_message = True
        lcd_message = self.message.text()
        self.status.setText("Waiting for guest response!")
        
    def StartOnClicked(self):
        print("Camera Started!")
    
    def openParcelOnClicked(self):
        global openParcel
        openParcel = True
        self.status.setText("Parcel Box is Opened.")

ESConnection = ArgonConnection()
ESConnectionThread = Thread(target=ESConnection.run)
ESConnectionThread.start()

Devices = ControlDevices()
DevicesThread = Thread(target=Devices.run)
DevicesThread.start()

GuestScreen = lcd()
GuestScreenThread = Thread(target=GuestScreen.run)
GuestScreenThread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = UI()
    
    # Update data on window objects every 1 second
    def update():
        global Temperature
        global Humidity
        global detected
        global Guest
        global GuestResponse
        global AirCon_status
        global Humidifier_status
        
        window.tempDisplay.display(Temperature)
        window.humDisplay.display(Humidity)
        window.motionStatus.setText(str(detected))
        window.guestStatus.setText(Guest)
        window.guessReply.setText(GuestResponse)
        window.airConStatus.setText(AirCon_status)
        window.humidifierStatus.setText(Humidifier_status)
        #particle_cloud.JustinArgon01.publish("Max_Temperature_Changed", str(window.maxTemp.value()))
        #particle_cloud.JustinArgon01.publish("Min_Temperature_Changed", str(window.minTemp.value()))
        
    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(1000)

    app.exec_()
    