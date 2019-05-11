# Message types
CONNECT = 0x1
CONNACK = 0x2
PUBLISH = 0x3
PUBACK = 0x4
PUBREC = 0x5
PUBREL = 0x6
PUBCOMP = 0x7
SUBSCRIBE = 0x8
SUBACK = 0x9
UNSUBSCRIBE = 0xA
UNSUBACK = 0xB
PINGREQ = 0xC
PINGRESP = 0xD
DISCONNECT = 0xE
# Connect
# data = b'\x10#\x00\x04MQTT\x04\x02\x00<\x00\x17mosq/qe5iYMiUyvMfMS5EuV'
# Connect
# data = b"\x10'\x00\x04MQTT\x04\x82\x00<\x00\
#               x17mosq/HvQcmIkWzkbhNk5ku7\x00\x02ro"
# data = b'0\x12\x00\x0bhouse/bulb2test3' #publish
# data = b'\x82\x0c\x00\x07\x00\x07house/#\x00' #subscribe
# data = b'\xc0\x00' #pingreq
# data = b'0\x06\x00\x02hote' #publish
# data = b'\xe0\x00'


class ByteMessage ():
    '''Byte Message send via mqtt protocol'''
    
    def __init__(self, data):
        self.data = data
        self.cursor = 0

    def next(self):
        d = self.data[self.cursor]
        self.cursor += 1
        return d

    def getText(self, length):
        res = ""
        for i in range(0, length):
            res += chr(self.next())
        return res

    def getInt(self, length):
        multiplier = 1
        for i in range(1, length):
            multiplier *= 128
        value = 0
        for i in range(0, length):
            encodedByte = self.next()
            value += encodedByte * multiplier
            multiplier /= 128
        return int(value)


class MQTTMessage ():
    """
        A generic MQTT message
        Field of the header
 
        :param data : A bytes messages
        
        :param messageType : type de message MQTT
        :param messageTypeStr : name of the type message
        :param flags :  flags of the MQTT message
        :param remainingLength : length of the rest of the message
    """
    def __init__(self, data):
        self.byteMessage = ByteMessage(data)
 
        controlHeader = self.byteMessage.next()
        self.messageType = (controlHeader & 0xF0) >> 4
        self.messageTypeStr = self.getMessageTypeStr()
        self.flags = controlHeader & 0x0F
        self.remainingLength = self.getRemainingLength(self.byteMessage)
        

    def __str__(self):
        return self.messageTypeStr

    def getMessageTypeStr(self):
        messageType = self.messageType
        if messageType == CONNECT:
            return 'CONNECT'
        elif messageType == CONNACK:
            return 'CONNACK'
        elif messageType == PUBLISH:
            return 'PUBLISH'
        elif messageType == PUBACK:
            return 'PUBACK'
        elif messageType == PUBREC:
            return 'PUBREC'
        elif messageType == PUBREL:
            return 'PUBREL'
        elif messageType == PUBCOMP:
            return 'PUBCOMP'
        elif messageType == SUBSCRIBE:
            return 'SUBSCRIBE'
        elif messageType == SUBACK:
            return 'SUBACK'
        elif messageType == UNSUBSCRIBE:
            return 'UNSUBSCRIBE'
        elif messageType == UNSUBACK:
            return 'UNSUBACK'
        elif messageType == PINGREQ:
            return 'PINGREQ'
        elif messageType == PINGRESP:
            return 'PINGRESP'
        elif messageType == DISCONNECT:
            return 'DISCONNECT'

    def getRemainingLength(self, byteMessage):
        multiplier = 1
        value = 0

        while True:
            encodedByte = byteMessage.next()
            value += (encodedByte & 127) * multiplier
            multiplier *= 128
            if (multiplier > 128*128*128):
                print('Malformed Remaining Length')
                SystemError(1)
            if ((encodedByte & 128) != 0):
                pass
            else:
                break
        return value


class MQTTConnectMessage(MQTTMessage):
    def __init__(self, data):
        MQTTMessage.__init__(self, data)
        self.lengthMSB = 0
        self.lengthLSB = 0
        self.protocolLevel = 0
        # connectFlag
        # userNameFlag
        # passwordFlag
        self.willRetain = 0
        self.willQoS = 0
        # willFlag
        self.cleanSession = 0
        self.reserved = 0
        self.KeepAliveMSB = 0
        self.KeepAliveLSB = 0
        self.clientID = ""
        self.willTopic = ""
        self.willMessage = ""
        self.userName = ""
        self.password = ""

    def __str__(self):
        return MQTTMessage.__str__(self) + " CLIENTID: " + self.clientID


class MQTTPublishMessage(MQTTMessage):
    def __init__(self, data):
        MQTTMessage.__init__(self, data)
        byteMessage = self.byteMessage
        # Fixed header
        self.QoS = (self.flags & 0x06) >> 1
        self.dup = (self.flags & 0x08) >> 3
        self.retain = (self.flags & 0x01)

        # Variable header
        self.lengthMSB = byteMessage.next()
        self.lengthLSB = byteMessage.next()

        self.topic = byteMessage.getText(self.lengthLSB)

        # self.packetidentifierMSB = byteMessage.next()
        # self.packetidentifierLSB = byteMessage.next()

        lengthVariableHeader = 1 + 1 + self.lengthMSB + self.lengthLSB
        payloadLength = self.remainingLength - lengthVariableHeader

        self.payload = byteMessage.getText(payloadLength)

    def __str__(self):
        return (MQTTMessage.__str__(self) +
                " PAYLOAD: " + self.payload +
                " TOPIC: " + self.topic)


class MQTTSubscribeMessage(MQTTMessage):
    def __init__(self, data):
        MQTTMessage.__init__(self, data)
        byteMessage = self.byteMessage

        # Variableheader
        self.packetidentifierMSB = byteMessage.next()
        self.packetidentifierLSB = byteMessage.next()

        lengthVariableHeader = 2
        payloadLength = self.remainingLength - lengthVariableHeader

        self.topicList = []
        while (payloadLength > 0):
            lengthMSB = byteMessage.next()
            lengthLSB = byteMessage.next()

            topicFilter = byteMessage.getText(lengthLSB)

            requestedQoS = byteMessage.next() & 0x02

            topic = {
                'lengthMSB': lengthMSB,
                'lengthLSB': lengthLSB,
                'topicFilter': topicFilter,
                'requestedQoS': requestedQoS
            }

            self.topicList.append(topic)
            payloadLength -= (3 + lengthLSB)

    def __str__(self):
        res = MQTTMessage.__str__(self)
        for topic in self.topicList:
            res += (" TOPIC: " + topic['topicFilter'] +
                    " QOS: " + str(topic['requestedQoS']))
        return res


def connect(data):
    #  ___________________________________________________________
    # |     1      |     2      |   3   |   4   |    5   |   6    |
    # |------------|------------|-------|-------|--------|--------|
    # | length MSB | length lsb |   M   |   Q   |   T    |   T    |
    # |____________|____________|_______|_______|________|________|
    #
    #  _________________________________________________________________
    # |       7        |       8       |       9        |       10      |
    # |----------------|---------------|----------------|---------------|
    # | protocol level | connect flags | keep alive mSB |keep alive lsb |
    # |________________|_______________|________________|_______________|
    # Connect flags :
    #           7 User Name Flag
    #           6 Password Flag
    #           5 Will Retain
    #           4 3 Will QoS
    #           2  Will Flag
    #           1 Clean Session
    #           0 Reserved
    #           byte 8 X X X X X X X 0
    #
    # Payload :  Client Identifier, Will Topic,
    #            Will Message, User Name, Password
    # Connect variable header 10
    m = MQTTConnectMessage(data)
    byteMessage = m.byteMessage

    # Variable header
    m.lengthMSB = byteMessage.next()
    m.lengthLSB = byteMessage.next()

    if (chr(byteMessage.next()) != 'M'):
        return
    if (chr(byteMessage.next()) != 'Q'):
        return
    if (chr(byteMessage.next()) != 'T'):
        return
    if (chr(byteMessage.next()) != 'T'):
        return

    m.protocolLevel = byteMessage.next()
    connectFlag = byteMessage.next()

    userNameFlag = (connectFlag & 0b10000000) >> 7
    passwordFlag = (connectFlag & 0b01000000) >> 6
    m.willRetain = (connectFlag & 0b00100000) >> 5
    m.willQoS = (connectFlag & 0b00011000) >> 3
    willFlag = (connectFlag & 0b00000100) >> 2
    m.cleanSession = (connectFlag & 0b00000010) >> 1
    m.reserved = (connectFlag & 0b00000001)

    m.KeepAliveMSB = byteMessage.next()
    m.KeepAliveLSB = byteMessage.next()

    clientIDLength = byteMessage.getInt(2)

    m.clientID = byteMessage.getText(clientIDLength)

    if willFlag:
        willTopicLength = byteMessage.getInt(2)
        m.willTopic = byteMessage.getText(willTopicLength)

        willMessageLength = byteMessage.getInt(2)
        m.willMessage = byteMessage.getText(willMessageLength)

    if userNameFlag:
        userNameLength = byteMessage.getInt(2)
        m.userName = byteMessage.getText(userNameLength)

    if passwordFlag:
        passwordLength = byteMessage.getInt(2)
        m.password = byteMessage.getText(passwordLength)

    return m


def handle_message_type(messageType, data):
    if messageType == CONNECT:
        return connect(data)
    elif messageType == PUBLISH:
        return MQTTPublishMessage(data)
    elif messageType == SUBSCRIBE:
        return MQTTSubscribeMessage(data)
    elif (messageType == CONNACK or
          messageType == PUBACK or
          messageType == PUBREC or
          messageType == PUBREL or
          messageType == PUBCOMP or
          messageType == SUBACK or
          messageType == UNSUBSCRIBE or
          messageType == UNSUBACK or
          messageType == PINGREQ or
          messageType == PINGRESP or
          messageType == DISCONNECT):
        return MQTTMessage(data)


def decodeMessage(data):
    messageType = (data[0] & 0xF0) >> 4
    return handle_message_type(messageType, data)

# decodeMessage(data)
