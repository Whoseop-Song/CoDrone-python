from enum import Enum


class DeviceType(Enum):
    None_ = 0x00
    DroneMain = 0x01    # Drone control
    DroneSub = 0x02     # Drone communication
    Link = 0x03         # Link module
    Tester = 0x04       # tester
    EndOfType = 0x05


class ImageType(Enum):
    None_ = 0x00
    # device image
    ImageA = 0x01
    ImageB = 0x02
    # firmware image
    RawImageA = 0x03
    RawImageB = 0x04
    # encrypted image
    EncryptedImageA = 0x05
    EncryptedImageB = 0x06
    # device image (CC253x / CC254x)
    ImageSingle = 0x07          # run Image
    RawImageSingle = 0x08       # uodate Image include header
    EncryptedImageSingle = 0x09 # uodate Image include header

    EndOfType = 0x0A


class ModeSystem(Enum):
    None_ = 0x00

    Boot = 0x01             # boot
    Wait = 0x02             # wait for connection
    Ready = 0x03            # ready
    Running = 0x04          # main code run
    Update = 0x05           # firmware update
    UpdateComplete = 0x06   # finish firmware update
    Error = 0x07            # firmware update error
    EndOfType = 0x08


class ModeVehicle(Enum):
    #mode for CoDrone
    None_ = 0x00
    FlightGuard = 0x10
    FlightNoGuard = 0x11
    FlightFPV = 0x12
    Drive = 0x20
    DriveFPV = 0x21
    Test = 0x30
    EndOfType = 0x31


class ModeFlight(Enum):
    None_ = 0x00
    Ready = 0x01    # ready
    TakeOff = 0x02  # take off (change to flight mode automatically)
    Flight = 0x03   # flight
    Flip = 0x04     # not support
    Stop = 0x05     # force stop(kill switch)
    Landing = 0x06  # Landing
    Reverse = 0x07  # upside down
    Accident = 0x08 # accident (change to ready mode automatically)
    Error = 0x09    # error
    EndOfType = 0x0A


class ModeDrive(Enum):
    #for drive mode(drive kit)
    None_ = 0x00
    Ready = 0x01  # ready
    Start = 0x02  # start
    Drive = 0x03  # drive
    Stop = 0x04   # force stop(kill stwich)
    Accident = 0x05  # accident (change to ready mode automatically)
    Error = 0x06  # error
    EndOfType = 0x07


class ModeUpdate(Enum):
    None_ = 0x00

    Ready = 0x01    # ready for modeupdate
    Update = 0x02   # updating
    Complete = 0x03 # finish update
    Faild = 0x04    # faild (ex : update finish but body's CRC16 is not match)
    EndOfType = 0x05


class ModeLink(Enum):
    None_ = 0x00

    Boot = 0x01  # boot
    Ready = 0x02  # ready(before connect)
    Connecting = 0x03  # connecting
    Connected = 0x04  # finish connection(normal connection)
    Disconnecting = 0x05  # disconnecting
    ReadyToReset = 0x06  # reset ready(reset after 1sec)

    EndOfType = 0x07


class ModeLinkBroadcast(Enum):
    None_ = 0x00

    Mute = 0x01  # block data request
    Active = 0x02  # data transport request and some auto thing
    Passive = 0x03 # reply just request things - no data transport when status is change, 연결 등의 상황에서는 진행 상황 전송

    EndOfType = 0x07


class EventLink(Enum):
    #bluetooth board

    None_ = 0x00
    SystemReset = 0x01
    Initialized = 0x02
    Scanning = 0x03
    ScanStop = 0x04
    FoundDroneService = 0x05
    Connecting = 0x06
    Connected = 0x07
    ConnectionFaild = 0x08
    ConnectionFaildNoDevices = 0x09
    ConnectionFaildNotReady = 0x0A
    PairingStart = 0x0B
    PairingSuccess = 0x0C
    PairingFaild = 0x0D
    BondingSuccess = 0x0E
    LookupAttribute = 0x0F

    RssiPollingStart = 0x10
    RssiPollingStop = 0x11
    DiscoverService = 0x12
    DiscoverCharacteristic = 0x13
    DiscoverCharacteristicDroneData = 0x14
    DiscoverCharacteristicDroneConfig = 0x15
    DiscoverCharacteristicUnknown = 0x16
    DiscoverCCCD = 0x17
    ReadyToControl = 0x18
    Disconnecting = 0x19
    Disconnected = 0x1A
    GapLinkParamUpdate = 0x1B  # GAP_LINK_PARAM_UPDATE_EVENT
    RspReadError = 0x1C
    RspReadSuccess = 0x1D
    RspWriteError = 0x1E
    RspWriteSuccess = 0x1F
    SetNotify = 0x20  # Notify activate
    Write = 0x21  # write event

    EndOfType = 0x22


class ModeLinkDiscover(Enum):
    None_ = 0x00

    Name = 0x01
    Service = 0x02
    All = 0x03

    EndOfType = 0x04


class FlightEvent(Enum):
    None_ = 0x00

    TakeOff = 0x01
    FlipFront = 0x02    # Reserved
    FlipRear = 0x03     # Reserved
    FlipLeft = 0x04     # Reserved
    FlipRight = 0x05    # Reserved
    Stop = 0x06     # force stop
    Landing = 0x07
    Reverse = 0x08  # upside down
    Shot = 0x09     # shoot IR missile
    UnderAttack = 0x0A  # be hitted by IR missile
    EndOfType = 0x0B


class DriveEvent(Enum):
    None_ = 0x00
    Stop = 0x01
    Shot = 0x02
    UnderAttack = 0x03
    EndOfType = 0x04


class Direction(Enum):
    None_ = 0x00
    Left = 0x01
    Front = 0x02
    Right = 0x03
    Rear = 0x04
    Top = 0x05
    Bottom = 0x06
    EndOfType = 0x07


class SensorOrientation(Enum):
    None_ = 0x00
    Normal = 0x01
    ReverseStart = 0x02
    Reversed = 0x03
    EndOfType = 0x04


class Headless(Enum):
    None_ = 0x00
    Headless = 0x01  # Headless
    Normal = 0x02  # Normal
    EndOfType = 0x03


class Trim(Enum):
    # increase or decrease will be 1
    None_ = 0x00
    RollIncrease = 0x01
    RollDecrease = 0x02
    PitchIncrease = 0x03
    PitchDecrease = 0x04
    YawIncrease = 0x05
    YawDecrease = 0x06
    ThrottleIncrease = 0x07
    ThrottleDecrease = 0x08
    Reset = 0x09  # reset all trim

    EndOfType = 0x0A


