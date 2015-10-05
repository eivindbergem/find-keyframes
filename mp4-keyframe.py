import cStringIO, struct, sys

TS_PACKET_SIZE = 188

class MpegTsFile:
    def __init__(self, filename):
        self.fd = open(filename, "rb")

    def find_sync(self):
        while True:
            pos = self.fd.tell()

            x = self.fd.read(1)

            if x == '\x47':
                self.fd.seek(-1, 1)
                if self.read_packet()[0] == '\x47':
                    self.fd.seek(pos)
                    break
                else:
                    self.fd.seek(pos+1)

    def read_packet(self):
        return self.fd.read(TS_PACKET_SIZE)

    def find(self, substr):
        bufsize = TS_PACKET_SIZE*32
        pos = self.fd.tell()
        buf = self.fd.read(bufsize)

        while True:
            if not buf:
                return ""

            buf_pos = buf.find(substr)

            if buf_pos == -1:
                pos = self.fd.tell()
                buf = self.fd.read(bufsize)
            else:
                pos = pos + buf_pos
                self.fd.seek(pos - (pos % 188))
                return self.read_packet()

        # while True:
        #     packet = self.read_packet()

        #     if not packet:
        #         return ""

        #     if packet.find(substr) != -1:
        #         return packet

        # return ""

    def seek(self, pos, whence=0):
        return self.fd.seek(pos, whence)

    def tell(self):
        return self.fd.tell()

class TSPacket:
    def __init__(self, data):
        self.data = data
        fd = cStringIO.StringIO(data)

        header = struct.unpack('>i', fd.read(4))[0]
        self.header = {"sync_byte": header >> 24,
                       "tei": header >> 23 & 0x1,
                       "payl_start": header >> 22 & 0x1,
                       "tp": header >> 21 & 0x1,
                       "pid": header >> 8 & 0x1fff,
                       "scram": header >> 6 & 0x3,
                       "adap_field": header >> 5 & 0x1,
                       "cont_payl": header >> 4 & 0x1,
                       "contin": header & 0xf}

        if self.header["adap_field"]:
            length = ord(fd.read(1))
            flags = ord(fd.read(1))
            fd.read(length - 1)

        if self.header['cont_payl']:
            self.stream_id = "\x00"

            self.start_code = fd.read(3)
            if self.start_code == '\x00\x00\x01':
                self.stream_id = fd.read(1)

                self.pes_length = struct.unpack('>H', fd.read(2))[0]


            self.payl = fd.read()

class Frame:
    def __init__(self, pos, size, is_keyframe, packet):
        self.pos = pos
        self.size = size
        self.is_keyframe = is_keyframe
        self.packet = packet
        self.duration = 0.0

    def __str__(self):
        return str(self.pos) + ":" + str(self.duration)

def get_iframes(filename):
    fd = MpegTsFile(filename)

    fd.find_sync()

    iframes = []

    last_keyframe = None

    while True:
        data = fd.find("\x00\x00\x01\xe0")
        pos = fd.tell() - TS_PACKET_SIZE

        if data:
            packet = TSPacket(data)

            if (packet.header["payl_start"] and
                packet.header["cont_payl"] and
                packet.stream_id == '\xe0'):

                if last_keyframe:
                    last_keyframe.duration += 0.0417

                data = fd.read_packet()

                if data:
                    next_packet = TSPacket(data)
                else:
                    next_packet = None

                keyframe = False

                for x in (packet, next_packet):
                    if not x:
                        continue

                    if (x.payl.find("\x00\x00\x01\x67") != -1 or
                        x.payl.find("\x00\x00\x01\x06") != -1):
                        keyframe = True
                        break

                if keyframe:
                    if fd.find("\x00\x00\x01\xe0"):
                        size = fd.tell() - pos
                        fd.seek(-TS_PACKET_SIZE, 1)
                    else:
                        size = fd.tell() - pos

                    frame = Frame(pos, size, keyframe, packet)

                    if frame.is_keyframe:
                        last_keyframe = frame
                        iframes.append(frame)

                #if packet.pes_length:
                #    fd.seek(packet.pes_length - (packet.pes_length %
                #                                 TS_PACKET_SIZE), 1)



        else:
            break

    return iframes
