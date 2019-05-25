import datetime

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

# MESSAGE EXEMPLE
# Connect
data = b'\x10#\x00\x04MQTT\x04\x02\x00<\x00\x17mosq/qe5iYMiUyvMfMS5EuV'
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

    def get_text(self, length):
        res = ""
        for i in range(0, length):
            res += chr(self.next())
        return res

    def get_int(self, length):
        multiplier = 1
        for i in range(1, length):
            multiplier *= 128
        value = 0
        for i in range(0, length):
            encoded_byte = self.next()
            value += encoded_byte * multiplier
            multiplier /= 128
        return int(value)


class MQTTMessage ():
    """
        A generic MQTT message
        Field of the header

        :param data : A bytes messages

        :param message_type : type de message MQTT
        :param message_type_str : name of the type message
        :param flags :  flags of the MQTT message
        :param remaining_length : length of the rest of the message
    """
    def __init__(self, data):
        self.byte_message = ByteMessage(data)

        control_header = self.byte_message.next()
        self.message_type = (control_header & 0xF0) >> 4
        self.message_type_str = self.get_message_type_str()
        self.flags = control_header & 0x0F
        self.remaining_length = self.get_remaining_length(self.byte_message)
        self.time = datetime.datetime.now()

    def __str__(self):
        return self.message_type_str

    def get_message_type_str(self):
        message_type = self.message_type
        if message_type == CONNECT:
            return 'CONNECT'
        elif message_type == CONNACK:
            return 'CONNACK'
        elif message_type == PUBLISH:
            return 'PUBLISH'
        elif message_type == PUBACK:
            return 'PUBACK'
        elif message_type == PUBREC:
            return 'PUBREC'
        elif message_type == PUBREL:
            return 'PUBREL'
        elif message_type == PUBCOMP:
            return 'PUBCOMP'
        elif message_type == SUBSCRIBE:
            return 'SUBSCRIBE'
        elif message_type == SUBACK:
            return 'SUBACK'
        elif message_type == UNSUBSCRIBE:
            return 'UNSUBSCRIBE'
        elif message_type == UNSUBACK:
            return 'UNSUBACK'
        elif message_type == PINGREQ:
            return 'PINGREQ'
        elif message_type == PINGRESP:
            return 'PINGRESP'
        elif message_type == DISCONNECT:
            return 'DISCONNECT'

    def get_remaining_length(self, byte_message):
        multiplier = 1
        value = 0

        while True:
            encoded_byte = byte_message.next()
            value += (encoded_byte & 127) * multiplier
            multiplier *= 128
            if (multiplier > 128*128*128):
                print('Malformed Remaining Length')
                SystemError(1)
            if ((encoded_byte & 128) != 0):
                pass
            else:
                break
        return value


class MQTTConnectMessage(MQTTMessage):
    def __init__(self, data):
        MQTTMessage.__init__(self, data)
        self.length_msb = 0
        self.length_lsb = 0
        self.protocol_level = 0
        # connect_flag
        # user_name_flag
        # password_flag
        self.will_retain = 0
        self.will_qos = 0
        # will_flag
        self.clean_session = 0
        self.reserved = 0
        self.keep_alive_msb = 0
        self.keep_alive_lsb = 0
        self.client_id = ""
        self.will_topic = ""
        self.will_message = ""
        self.user_name = ""
        self.password = ""

    def __str__(self):
        return MQTTMessage.__str__(self) + " CLIENTID: " + self.client_id


class MQTTPublishMessage(MQTTMessage):

    """
        # Fixed header
        :param QoS
        :param dup
        :param retain

        # Variable header
        :param length_msb
        :param length_lsb

        :param topic
        :param packetidentifierMSB
        :param packetidentifierLSB

        :param payload
    """
    def __init__(self, data):
        MQTTMessage.__init__(self, data)
        byte_message = self.byte_message
        # Fixed header
        self.qos = (self.flags & 0x06) >> 1
        self.dup = (self.flags & 0x08) >> 3
        self.retain = (self.flags & 0x01)

        # Variable header
        self.length_msb = byte_message.next()
        self.length_lsb = byte_message.next()

        self.topic = byte_message.get_text(self.length_lsb)

        # self.packetidentifier_msb = byte_message.next()
        # self.packetidentifier_lsb = byte_message.next()

        length_variable_header = 1 + 1 + self.length_msb + self.length_lsb
        payload_length = self.remaining_length - length_variable_header

        self.payload = byte_message.get_text(payload_length)

    def __str__(self):
        return (MQTTMessage.__str__(self) +
                " PAYLOAD: " + self.payload +
                " TOPIC: " + self.topic)


class MQTTSubscribeMessage(MQTTMessage):
    """
        : param packetidentifier_msb
        : param packetidentifier_lsb
        : param topic_list
                    {
                        'length_msb': length_msb,
                        'length_lsb': length_lsb,
                        'topic_filter': topic_filter,
                        'requested_qos': requested_qos
                    }
    """

    def __init__(self, data):

        MQTTMessage.__init__(self, data)
        byte_message = self.byte_message

        # Variableheader
        self.packetidentifier_msb = byte_message.next()
        self.packetidentifier_lsb = byte_message.next()

        length_variable_header = 2
        payload_length = self.remaining_length - length_variable_header

        self.topic_list = []
        while (payload_length > 0):
            length_msb = byte_message.next()
            length_lsb = byte_message.next()

            topic_filter = byte_message.get_text(length_lsb)

            requested_qos = byte_message.next() & 0x02

            topic = {
                'length_msb': length_msb,
                'length_lsb': length_lsb,
                'topic_filter': topic_filter,
                'requested_qos': requested_qos
            }

            self.topic_list.append(topic)
            payload_length -= (3 + length_lsb)

    def __str__(self):
        res = MQTTMessage.__str__(self)
        for topic in self.topic_list:
            res += (" TOPIC: " + topic['topic_filter'] +
                    " QOS: " + str(topic['requested_qos']))
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
    byte_message = m.byte_message

    # Variable header
    m.length_msb = byte_message.next()
    m.length_lsb = byte_message.next()

    a = byte_message.next()
    if (chr(a) != 'M'):
        return
    a = byte_message.next()
    if (chr(a) != 'Q'):
        return
    a = byte_message.next()
    if (chr(a) != 'T'):
        return
    a = byte_message.next()
    if (chr(a) != 'T'):
        return

    # MQIsdp

    # if (
    #     chr(byte_message.next()) != 'I' or
    #     chr(byte_message.next()) != 's' or
    #     chr(byte_message.next()) != 'd' or
    #     chr(byte_message.next()) != 'p'
    #    ):
    #     return

    m.protocol_level = byte_message.next()
    connect_flag = byte_message.next()

    user_name_flag = (connect_flag & 0b10000000) >> 7
    password_flag = (connect_flag & 0b01000000) >> 6
    m.will_retain = (connect_flag & 0b00100000) >> 5
    m.will_qos = (connect_flag & 0b00011000) >> 3
    will_flag = (connect_flag & 0b00000100) >> 2
    m.clean_session = (connect_flag & 0b00000010) >> 1
    m.reserved = (connect_flag & 0b00000001)

    m.keep_alive_msb = byte_message.next()
    m.keep_alive_lsb = byte_message.next()

    client_id_length = byte_message.get_int(2)

    m.client_id = byte_message.get_text(client_id_length)

    if will_flag:
        will_topic_length = byte_message.get_int(2)
        m.will_topic = byte_message.get_text(will_topic_length)

        will_message_length = byte_message.get_int(2)
        m.will_message = byte_message.get_text(will_message_length)

    if user_name_flag:
        user_name_length = byte_message.get_int(2)
        m.user_name = byte_message.get_text(user_name_length)

    if password_flag:
        password_length = byte_message.get_int(2)
        m.password = byte_message.get_text(password_length)

    return m


def handle_message_type(message_type, data):
    if message_type == CONNECT:
        return connect(data)
    elif message_type == PUBLISH:
        return MQTTPublishMessage(data)
    elif message_type == SUBSCRIBE:
        return MQTTSubscribeMessage(data)
    elif (message_type == CONNACK or
          message_type == PUBACK or
          message_type == PUBREC or
          message_type == PUBREL or
          message_type == PUBCOMP or
          message_type == SUBACK or
          message_type == UNSUBSCRIBE or
          message_type == UNSUBACK or
          message_type == PINGREQ or
          message_type == PINGRESP or
          message_type == DISCONNECT):
        return MQTTMessage(data)


def decode_message(data):
    message_type = (data[0] & 0xF0) >> 4
    return handle_message_type(message_type, data)


# decode_message(data)
