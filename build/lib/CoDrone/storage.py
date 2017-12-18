from CoDrone.system import *

from CoDrone.protocol import *


# EventHandler
class EventHandler:
    def __init__(self):
        self.d = dict.fromkeys(list(DataType))


# StorageHeader
class StorageHeader:
    def __init__(self):
        self.d = dict.fromkeys(list(DataType))


# Storage
class Storage:
    def __init__(self):
        self.d = dict.fromkeys(list(DataType))


# Storage Count
class StorageCount:
    def __init__(self):
        self.d = dict.fromkeys(list(DataType))

        for key in self.d:
            self.d[key] = 0


# Storage
class Parser:
    def __init__(self):
        self.d = dict.fromkeys(list(DataType))

        self.d[DataType.Ping] = Ping.parse
        self.d[DataType.Ack] = Ack.parse
        self.d[DataType.Request] = Request.parse
        self.d[DataType.Passcode] = Passcode.parse

        self.d[DataType.Address] = Address.parse
        self.d[DataType.State] = State.parse
        self.d[DataType.Attitude] = Attitude.parse
        self.d[DataType.GyroBias] = GyroBias.parse
        self.d[DataType.TrimFlight] = TrimFlight.parse
        self.d[DataType.TrimDrive] = TrimDrive.parse
        self.d[DataType.TrimAll] = TrimAll.parse

        self.d[DataType.CountFlight] = CountFlight.parse
        self.d[DataType.CountDrive] = CountDrive.parse
        self.d[DataType.IrMessage] = IrMessage.parse

        self.d[DataType.Imu] = Imu.parse
        self.d[DataType.Pressure] = Pressure.parse
        self.d[DataType.ImageFlow] = ImageFlow.parse
        self.d[DataType.Button] = Button.parse
        self.d[DataType.Battery] = Battery.parse
        self.d[DataType.Motor] = Motor.parse
        self.d[DataType.Temperature] = Temperature.parse
        self.d[DataType.Range] = Range.parse

        self.d[DataType.UpdateInformation] = UpdateInformation.parse
        self.d[DataType.UpdateLocationCorrect] = UpdateLocationCorrect.parse

        self.d[DataType.LinkState] = LinkState.parse
        self.d[DataType.LinkEvent] = LinkEvent.parse
        self.d[DataType.LinkEventAddress] = LinkEventAddress.parse
        self.d[DataType.LinkRssi] = LinkRssi.parse
        self.d[DataType.LinkDiscoveredDevice] = LinkDiscoveredDevice.parse
        self.d[DataType.LinkPasscode] = LinkPasscode.parse

        self.d[DataType.Message] = Message.parse

