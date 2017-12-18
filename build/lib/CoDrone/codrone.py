from operator import eq
from queue import Queue
from threading import Thread
from time import sleep

import colorama
import serial
from colorama import Fore, Back, Style
from CoDrone.crc import *
from CoDrone.receiver import *
from serial.tools.list_ports import comports
from CoDrone.system import *

from CoDrone.storage import *


def convertByteArrayToString(dataArray):
    if dataArray == None:
        return ""

    string = ""

    if (isinstance(dataArray, bytes)) or (isinstance(dataArray, bytearray)) or (not isinstance(dataArray, list)):
        for data in dataArray:
            string += "{0:02X} ".format(data)

    return string


class CoDrone:
    # BaseFunctions Start

    def __init__(self, flagCheckBackground=True, flagShowErrorMessage=False, flagShowLogMessage=False,
                 flagShowTransferData=False, flagShowReceiveData=False):

        self._serialport = None
        self._bufferQueue = Queue(4096)
        self._bufferHandler = bytearray()
        self._index = 0

        self._thread = None
        self._flagThreadRun = False

        self._receiver = Receiver()

        self._flagCheckBackground = flagCheckBackground

        self._flagShowErrorMessage = flagShowErrorMessage
        self._flagShowLogMessage = flagShowLogMessage
        self._flagShowTransferData = flagShowTransferData
        self._flagShowReceiveData = flagShowReceiveData

        self._eventHandler = EventHandler()
        self._storageHeader = StorageHeader()
        self._storage = Storage()
        self._storageCount = StorageCount()
        self._parser = Parser()

        self._devices = []          # when using auto connect, save search list
        self._flagDiscover = False  # when using auto connect, notice is discover
        self._flagConnected = False  # when using auto connect, notice connection with device
        self.timeStartProgram = time.time()  # record program starting time

        colorama.init()

    def __del__(self):
        self.close()

    def _receiving(self):
        while self._flagThreadRun:

            self._bufferQueue.put(self._serialport.read())
            # auto-update when background check for receive data is on
            if self._flagCheckBackground == True:
                while self.check() != DataType.None_:
                    pass

                    # sleep(0.001)

    def isOpen(self):
        if self._serialport != None:
            return self._serialport.isOpen()
        else:
            return False

    def isConnected(self):
        if self.isOpen() == False:
            return False
        else:
            return self._flagConnected

    def open(self, portName="None"):
        if eq(portName, "None"):
            nodes = comports()
            size = len(nodes)
            if size > 0:
                portName = nodes[size - 1].device
            else:
                return False

        self._serialport = serial.Serial(
            port=portName,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0)

        if (self.isOpen()):
            self._flagThreadRun = True
            self._thread = Thread(target=self._receiving, args=(), daemon=True).start()

            # print log
            self._printLog("Connected.({0})".format(portName))

            return True
        else:
            # print error message
            self._printError("Could not connect to PETRONE LINK.")

            return False

    def close(self):
        # print log
        if self.isOpen():
            self._printLog("Closing serial port.")

        if self._flagThreadRun == True:
            self._flagThreadRun = False
            sleep(0.01)

        if self._thread != None:
            self._thread.join()

        while (self.isOpen() == True):
            self._serialport.close()
            sleep(0.01)

    def makeTransferDataArray(self, header, data):
        if (header == None) or (data == None):
            return None

        if (not isinstance(header, Header)) or (not isinstance(data, ISerializable)):
            return None

        crc16 = CRC16.calc(header.toArray(), 0)
        crc16 = CRC16.calc(data.toArray(), crc16)

        dataArray = bytearray()
        dataArray.extend((0x0A, 0x55))
        dataArray.extend(header.toArray())
        dataArray.extend(data.toArray())
        dataArray.extend(pack('H', crc16))

        return dataArray

    def transfer(self, header, data):
        if not self.isOpen():
            return

        dataArray = self.makeTransferDataArray(header, data)

        self._serialport.write(dataArray)

        # print transfer data
        self._printTransferData(dataArray)

        return dataArray

    def check(self):
        while self._bufferQueue.empty() == False:
            dataArray = self._bufferQueue.get_nowait()
            self._bufferQueue.task_done()

            if (dataArray != None) and (len(dataArray) > 0):
                # print receive data
                self._printReceiveData(dataArray)

                self._bufferHandler.extend(dataArray)

        while len(self._bufferHandler) > 0:
            stateLoading = self._receiver.call(self._bufferHandler.pop(0))

            # print error
            if stateLoading == StateLoading.Failure:
                # print receive data
                self._printReceiveDataEnd()

                # print error
                self._printError(self._receiver.message)

            # print log
            if stateLoading == StateLoading.Loaded:
                # print receive data
                self._printReceiveDataEnd()

                # print log
                self._printLog(self._receiver.message)

            if self._receiver.state == StateLoading.Loaded:
                self._handler(self._receiver.header, self._receiver.data)
                return self._receiver.header.dataType

        return DataType.None_

    def checkDetail(self):
        while self._bufferQueue.empty() == False:
            dataArray = self._bufferQueue.get_nowait()
            self._bufferQueue.task_done()

            if (dataArray != None) and (len(dataArray) > 0):
                # print receive data
                self._printReceiveData(dataArray)

                self._bufferHandler.extend(dataArray)

        while len(self._bufferHandler) > 0:
            stateLoading = self._receiver.call(self._bufferHandler.pop(0))

            # ptint error
            if stateLoading == StateLoading.Failure:
                # print receive data
                self._printReceiveDataEnd()

                # print error
                self._printError(self._receiver.message)

            # print log
            if stateLoading == StateLoading.Loaded:
                # print receive data
                self._printReceiveDataEnd()

                # print log
                self._printLog(self._receiver.message)

            if self._receiver.state == StateLoading.Loaded:
                self._handler(self._receiver.header, self._receiver.data)
                return self._receiver.header, self._receiver.data

        return None, None

    def _handler(self, header, dataArray):

        # save input data
        message = self._runHandler(header, dataArray)

        # print error
        if (message != None):
            self._printError(message)

        # run callback event
        self._runEventHandler(header.dataType)

        # process LinkEvent separately(event check like connect or disconnect)
        if (header.dataType == DataType.LinkEvent) and (self._storage.d[DataType.LinkEvent] != None):
            self._eventLinkEvent(self._storage.d[DataType.LinkEvent])

        # process LinkEventAddress separately(event check like connect or disconnect)
        if (header.dataType == DataType.LinkEventAddress) and (self._storage.d[DataType.LinkEventAddress] != None):
            self._eventLinkEventAddress(self._storage.d[DataType.LinkEventAddress])

        # process LinkDiscoveredDevice separately(add list of searched device)
        if (header.dataType == DataType.LinkDiscoveredDevice) and (
            self._storage.d[DataType.LinkDiscoveredDevice] != None):
            self._eventLinkDiscoveredDevice(self._storage.d[DataType.LinkDiscoveredDevice])

        # complete data process
        self._receiver.checked()

        return header.dataType

    def _runHandler(self, header, dataArray):
        if self._parser.d[header.dataType] != None:
            self._storageHeader.d[header.dataType] = header
            self._storage.d[header.dataType] = self._parser.d[header.dataType](dataArray);
            self._storageCount.d[header.dataType] += 1

    def _runEventHandler(self, dataType):
        if (isinstance(dataType, DataType)) and (self._eventHandler.d[dataType] != None) and (
            self._storage.d[dataType] != None):
            return self._eventHandler.d[dataType](self._storage.d[dataType])
        else:
            return None

    def setEventHandler(self, dataType, eventHandler):

        if (not isinstance(dataType, DataType)):
            return

        self._eventHandler.d[dataType] = eventHandler

    def getHeader(self, dataType):

        if (not isinstance(dataType, DataType)):
            return None

        return self._storageHeader.d[dataType]

    def getData(self, dataType):

        if (not isinstance(dataType, DataType)):
            return None

        return self._storage.d[dataType]

    def getCount(self, dataType):

        if (not isinstance(dataType, DataType)):
            return None

        return self._storageCount.d[dataType]

    def _eventLinkHandler(self, eventLink):
        if eventLink == EventLink.Scanning:
            self._devices.clear()
            self._flagDiscover = True

        elif eventLink == EventLink.ScanStop:
            self._flagDiscover = False

        elif eventLink == EventLink.Connected:
            self._flagConnected = True

        elif eventLink == EventLink.Disconnected:
            self._flagConnected = False

        # print log
        self._printLog(eventLink)

    def _eventLinkEvent(self, data):
        self._eventLinkHandler(data.eventLink)

    def _eventLinkEventAddress(self, data):
        self._eventLinkHandler(data.eventLink)

    def _eventLinkDiscoveredDevice(self, data):
        self._devices.append(data)

        # print log
        self._printLog(
            "LinkDiscoveredDevice / {0} / {1} / {2} / {3}".format(data.index, convertByteArrayToString(data.address),
                                                                  data.name, data.rssi))

    def connect(self, portName="None", deviceName="None", flagSystemReset=False):

        # case for serial port is None(connect to last connection)
        if not self.isOpen():
            self.close()
            self.open(portName)
            sleep(0.1)

        # if not connect with serial port print error and return
        if not self.isOpen():
            # print error
            self._printError("Could not connect to PETRONE LINK.")

            return False

        # system reset
        if flagSystemReset:
            self.sendLinkSystemReset()
            sleep(3)

        # ModeLinkBroadcast.Passive mode change
        self.sendLinkModeBroadcast(ModeLinkBroadcast.Passive)
        sleep(0.1)

        # start searching device
        self._devices.clear()
        self._flagDiscover = True
        self.sendLinkDiscoverStart()

        # wait for 5sec
        for i in range(50):
            sleep(0.1)
            if not self._flagDiscover:
                break

        sleep(2)

        length = len(self._devices)

        if eq(deviceName, "None"):
            # 이름을 정하지 않은 경우 가장 가까운 장치에 연결
            if length > 0:
                closestDevice = self._devices[0]

                # 장치가 2개 이상 검색된 경우 가장 가까운 장치를 선택
                if len(self._devices) > 1:
                    for i in range(len(self._devices)):
                        if closestDevice.rssi < self._devices[i].rssi:
                            closestDevice = self._devices[i]

                # 장치 연결
                self._flagConnected = False
                self.sendLinkConnect(closestDevice.index)

                # 5초간 장치 연결을 기다림
                for i in range(50):
                    sleep(0.1)
                    if self._flagConnected:
                        break

                # 연결된 후 1.2초를 추가로 기다림
                sleep(1.2)

            else:
                # 오류 출력
                self._printError("Could not find PETRONE.")

        else:
            # 연결된 장치들의 이름 확인
            targetDevice = None

            if (len(self._devices) > 0):
                if (len(deviceName) == 12):
                    for i in range(len(self._devices)):

                        if (len(self._devices[i].name) > 12) and (deviceName == self._devices[i].name[0:12]):
                            targetDevice = self._devices[i]
                            break;

                    if targetDevice != None:
                        # 장치를 찾은 경우 연결
                        self._flagConnected = False
                        self.sendLinkConnect(targetDevice.index)

                        # 5초간 장치 연결을 기다림
                        for i in range(50):
                            sleep(0.1)
                            if self._flagConnected:
                                break

                        # 연결된 후 1.2초를 추가로 기다림
                        sleep(1.2)

                    else:
                        # 오류 출력
                        self._printError("Could not find " + deviceName + ".")

                else:
                    # 오류 출력
                    self._printError("Device name length error(" + deviceName + ").")

            else:
                # 오류 출력
                self._printError("Could not find PETRONE.")

        return self._flagConnected

    def _printLog(self, message):

        # 로그 출력
        if self._flagShowLogMessage and message != None:
            print(Fore.GREEN + "[{0:10.03f}] {1}".format((time.time() - self.timeStartProgram),
                                                         message) + Style.RESET_ALL)

    def _printError(self, message):

        # 오류 메세지 출력
        if self._flagShowErrorMessage and message != None:
            print(
                Fore.RED + "[{0:10.03f}] {1}".format((time.time() - self.timeStartProgram), message) + Style.RESET_ALL)

    def _printTransferData(self, dataArray):

        # 송신 데이터 출력
        if (self._flagShowTransferData) and (dataArray != None) and (len(dataArray) > 0):
            print(Back.YELLOW + Fore.BLACK + convertByteArrayToString(dataArray) + Style.RESET_ALL)

    def _printReceiveData(self, dataArray):

        # 수신 데이터 출력
        if (self._flagShowReceiveData) and (dataArray != None) and (len(dataArray) > 0):
            print(Back.CYAN + Fore.BLACK + convertByteArrayToString(dataArray) + Style.RESET_ALL, end='')

    def _printReceiveDataEnd(self):

        # 수신 데이터 출력(줄넘김)
        if self._flagShowReceiveData:
            print("")


            # BaseFunctions End



            # Common Start

    def sendPing(self):

        header = Header()

        header.dataType = DataType.Ping
        header.length = Ping.getSize()

        data = Ping()

        data.systemTime = 0

        return self.transfer(header, data)

    def sendRequest(self, dataType):

        if (not isinstance(dataType, DataType)):
            return None

        header = Header()

        header.dataType = DataType.Request
        header.length = Request.getSize()

        data = Request()

        data.dataType = dataType

        return self.transfer(header, data)

    # Common Start



    # Control Start


    def sendTakeOff(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.FlightEvent
        data.option = FlightEvent.TakeOff.value

        return self.transfer(header, data)

    def sendLanding(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.FlightEvent
        data.option = FlightEvent.Landing.value

        return self.transfer(header, data)

    def sendStop(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.Stop
        data.option = 0

        return self.transfer(header, data)

    def sendControl(self, roll, pitch, yaw, throttle):

        if ((not isinstance(roll, int)) or (not isinstance(pitch, int)) or (not isinstance(yaw, int)) or (
        not isinstance(throttle, int))):
            return None

        header = Header()

        header.dataType = DataType.Control
        header.length = Control.getSize()

        data = Control()

        data.roll = roll
        data.pitch = pitch
        data.yaw = yaw
        data.throttle = throttle

        return self.transfer(header, data)

    def sendControlWhile(self, roll, pitch, yaw, throttle, timeMs):

        if ((not isinstance(roll, int)) or (not isinstance(pitch, int)) or (not isinstance(yaw, int)) or (
        not isinstance(throttle, int))):
            return None

        timeSec = timeMs / 1000
        timeStart = time.time()

        while ((time.time() - timeStart) < timeSec):
            self.sendControl(roll, pitch, yaw, throttle)
            sleep(0.02)

        return self.sendControl(roll, pitch, yaw, throttle)

    def sendControlDrive(self, wheel, accel):

        if ((not isinstance(wheel, int)) or (not isinstance(accel, int))):
            return None

        header = Header()

        header.dataType = DataType.Control
        header.length = Control.getSize()

        data = Control()

        data.roll = accel
        data.pitch = 0
        data.yaw = 0
        data.throttle = wheel

        return self.transfer(header, data)

    def sendControlDriveWhile(self, wheel, accel, timeMs):

        if ((not isinstance(wheel, int)) or (not isinstance(accel, int))):
            return None

        timeSec = timeMs / 1000
        timeStart = time.time()

        while ((time.time() - timeStart) < timeSec):
            self.sendControlDrive(wheel, accel)
            sleep(0.02)

        return self.sendControlDrive(wheel, accel)

    # Control End



    # Setup Start


    def sendCommand(self, commandType, option=0):

        if ((not isinstance(commandType, CommandType)) or (not isinstance(option, int))):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = commandType
        data.option = option

        return self.transfer(header, data)

    def sendModeVehicle(self, modeVehicle):

        if (not isinstance(modeVehicle, ModeVehicle)):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.ModeVehicle
        data.option = modeVehicle.value

        return self.transfer(header, data)

    def sendHeadless(self, headless):

        if (not isinstance(headless, Headless)):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.Headless
        data.option = headless.value

        return self.transfer(header, data)

    def sendTrim(self, trim):

        if ((not isinstance(trim, Trim))):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.Trim
        data.option = trim.value

        return self.transfer(header, data)

    def sendTrimFlight(self, roll, pitch, yaw, throttle):

        if ((not isinstance(roll, int)) or (not isinstance(pitch, int)) or (not isinstance(yaw, int)) or (
        not isinstance(throttle, int))):
            return None

        header = Header()

        header.dataType = DataType.TrimFlight
        header.length = TrimFlight.getSize()

        data = TrimFlight()

        data.roll = roll
        data.pitch = pitch
        data.yaw = yaw
        data.throttle = throttle

        return self.transfer(header, data)

    def sendTrimDrive(self, wheel):

        if (not isinstance(wheel, int)):
            return None

        header = Header()

        header.dataType = DataType.TrimDrive
        header.length = TrimDrive.getSize()

        data = TrimDrive()

        data.wheel = wheel

        return self.transfer(header, data)

    def sendFlightEvent(self, flightEvent):

        if ((not isinstance(flightEvent, FlightEvent))):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.FlightEvent
        data.option = flightEvent.value

        return self.transfer(header, data)

    def sendDriveEvent(self, driveEvent):

        if ((not isinstance(driveEvent, DriveEvent))):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.DriveEvent
        data.option = driveEvent.value

        return self.transfer(header, data)

    def sendClearTrim(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.ClearTrim
        data.option = 0

        return self.transfer(header, data)

    def sendClearGyroBias(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.ClearGyroBias
        data.option = 0

        return self.transfer(header, data)

    def sendUpdateLookupTarget(self, deviceType):

        if ((not isinstance(deviceType, DeviceType))):
            return None

        header = Header()

        header.dataType = DataType.UpdateLookupTarget
        header.length = UpdateLookupTarget.getSize()

        data = UpdateLookupTarget()

        data.deviceType = deviceType

        return self.transfer(header, data)

    # Setup End



    # Device Start

    def sendMotor(self, motor0, motor1, motor2, motor3):

        if ((not isinstance(motor0, int)) or
                (not isinstance(motor1, int)) or
                (not isinstance(motor2, int)) or
                (not isinstance(motor3, int))):
            return None

        header = Header()

        header.dataType = DataType.Motor
        header.length = Motor.getSize()

        data = Motor()

        data.motor[0].forward = motor0
        data.motor[0].reverse = 0

        data.motor[1].forward = motor1
        data.motor[1].reverse = 0

        data.motor[2].forward = motor2
        data.motor[2].reverse = 0

        data.motor[3].forward = motor3
        data.motor[3].reverse = 0

        return self.transfer(header, data)

    def sendIrMessage(self, value):

        if ((not isinstance(value, int))):
            return None

        header = Header()

        header.dataType = DataType.IrMessage
        header.length = IrMessage.getSize()

        data = IrMessage()

        data.irData = value

        return self.transfer(header, data)

    # Device End



    # Light Start


    def sendLightMode(self, lightMode, colors, interval):

        if (((not isinstance(lightMode, LightMode))) or
                (not isinstance(interval, int)) or
                (not isinstance(colors, Colors))):
            return None

        header = Header()

        header.dataType = DataType.LightMode
        header.length = LightMode.getSize()

        data = LightMode()

        data.mode = lightMode
        data.colors = colors
        data.interval = interval

        return self.transfer(header, data)

    def sendLightModeCommand(self, lightMode, colors, interval, commandType, option):

        if (((not isinstance(lightMode, LightMode))) or
                (not isinstance(interval, int)) or
                (not isinstance(colors, Colors)) or
                (not isinstance(commandType, CommandType)) or
                (not isinstance(option, int))):
            return None

        header = Header()

        header.dataType = DataType.LightModeCommand
        header.length = LightModeCommand.getSize()

        data = LightModeCommand()

        data.mode.mode = lightMode
        data.mode.colors = colors
        data.mode.interval = interval

        data.command.commandType = commandType
        data.command.option = option

        return self.transfer(header, data)

    def sendLightModeCommandIr(self, lightMode, interval, colors, commandType, option, irData):

        if (((not isinstance(lightMode, LightMode))) or
                (not isinstance(interval, int)) or
                (not isinstance(colors, Colors)) or
                (not isinstance(commandType, CommandType)) or
                (not isinstance(option, int)) or
                (not isinstance(irData, int))):
            return None

        header = Header()

        header.dataType = DataType.LightModeCommandIr
        header.length = LightModeCommandIr.getSize()

        data = LightModeCommandIr()

        data.mode.mode = lightMode
        data.mode.colors = colors
        data.mode.interval = interval

        data.command.commandType = commandType
        data.command.option = option

        data.irData = irData

        return self.transfer(header, data)

    def sendLightModeColor(self, lightMode, r, g, b, interval):

        if ((not isinstance(lightMode, LightMode)) or
                (not isinstance(r, int)) or
                (not isinstance(g, int)) or
                (not isinstance(b, int)) or
                (not isinstance(interval, int))):
            return None

        header = Header()

        header.dataType = DataType.LightModeColor
        header.length = LightModeColor.getSize()

        data = LightModeColor()

        data.mode = lightMode
        data.color.r = r
        data.color.g = g
        data.color.b = b
        data.interval = interval

        return self.transfer(header, data)

    def sendLightEvent(self, lightEvent, colors, interval, repeat):

        if (((not isinstance(lightEvent, LightMode))) or
                (not isinstance(colors, Colors)) or
                (not isinstance(interval, int)) or
                (not isinstance(repeat, int))):
            return None

        header = Header()

        header.dataType = DataType.LightEvent
        header.length = LightEvent.getSize()

        data = LightEvent()

        data.event = lightEvent
        data.colors = colors
        data.interval = interval
        data.repeat = repeat

        return self.transfer(header, data)

    def sendLightEventCommand(self, lightEvent, colors, interval, repeat, commandType, option):

        if (((not isinstance(lightEvent, LightMode))) or
                (not isinstance(colors, Colors)) or
                (not isinstance(interval, int)) or
                (not isinstance(repeat, int)) or
                (not isinstance(commandType, CommandType)) or
                (not isinstance(option, int))):
            return None

        header = Header()

        header.dataType = DataType.LightEventCommand
        header.length = LightEventCommand.getSize()

        data = LightEventCommand()

        data.event.event = lightEvent
        data.event.colors = colors
        data.event.interval = interval
        data.event.repeat = repeat

        data.command.commandType = commandType
        data.command.option = option

        return self.transfer(header, data)

    def sendLightEventCommandIr(self, lightEvent, colors, interval, repeat, commandType, option, irData):

        if (((not isinstance(lightEvent, LightMode))) or
                (not isinstance(colors, Colors)) or
                (not isinstance(interval, int)) or
                (not isinstance(repeat, int)) or
                (not isinstance(commandType, CommandType)) or
                (not isinstance(option, int)) or
                (not isinstance(irData, int))):
            return None

        header = Header()

        header.dataType = DataType.LightEventCommandIr
        header.length = LightEventCommandIr.getSize()

        data = LightEventCommandIr()

        data.event.event = lightEvent
        data.event.colors = colors
        data.event.interval = interval
        data.event.repeat = repeat

        data.command.commandType = commandType
        data.command.option = option

        data.irData = irData

        return self.transfer(header, data)

    def sendLightEventColor(self, lightEvent, r, g, b, interval, repeat):

        if (((not isinstance(lightEvent, LightMode))) or
                (not isinstance(r, int)) or
                (not isinstance(g, int)) or
                (not isinstance(b, int)) or
                (not isinstance(interval, int)) or
                (not isinstance(repeat, int))):
            return None

        header = Header()

        header.dataType = DataType.LightEventColor
        header.length = LightEventColor.getSize()

        data = LightEventColor()

        data.event = lightEvent.value
        data.color.r = r
        data.color.g = g
        data.color.b = b
        data.interval = interval
        data.repeat = repeat

        return self.transfer(header, data)

    def sendLightModeDefaultColor(self, lightMode, r, g, b, interval):

        if ((not isinstance(lightMode, LightMode)) or
                (not isinstance(r, int)) or
                (not isinstance(g, int)) or
                (not isinstance(b, int)) or
                (not isinstance(interval, int))):
            return None

        header = Header()

        header.dataType = DataType.LightModeDefaultColor
        header.length = LightModeDefaultColor.getSize()

        data = LightModeDefaultColor()

        data.mode = lightMode
        data.color.r = r
        data.color.g = g
        data.color.b = b
        data.interval = interval

        return self.transfer(header, data)

    # Light End



    # Link Start


    def sendLinkModeBroadcast(self, modeLinkBroadcast):

        if (not isinstance(modeLinkBroadcast, ModeLinkBroadcast)):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkModeBroadcast
        data.option = modeLinkBroadcast.value

        return self.transfer(header, data)

    def sendLinkSystemReset(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkSystemReset
        data.option = 0

        return self.transfer(header, data)

    def sendLinkDiscoverStart(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkDiscoverStart
        data.option = 0

        return self.transfer(header, data)

    def sendLinkDiscoverStop(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkDiscoverStop
        data.option = 0

        return self.transfer(header, data)

    def sendLinkConnect(self, index):

        if (not isinstance(index, int)):
            return None

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkConnect
        data.option = index

        return self.transfer(header, data)

    def sendLinkDisconnect(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkDisconnect
        data.option = 0

        return self.transfer(header, data)

    def sendLinkRssiPollingStart(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkRssiPollingStart
        data.option = 0

        return self.transfer(header, data)

    def sendLinkRssiPollingStop(self):

        header = Header()

        header.dataType = DataType.Command
        header.length = Command.getSize()

        data = Command()

        data.commandType = CommandType.LinkRssiPollingStop
        data.option = 0

        return self.transfer(header, data)

# Vibrator End

