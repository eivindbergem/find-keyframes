# Copyright 2015 Eivind Alexander Bergem <eivind.bergem@gmail.com>
#
# This file is part of find-keyframes.
#
# find-keyframes is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with find-keyframes.  If not, see <http://www.gnu.org/licenses/>.

import cStringIO, struct, sys

TS_PACKET_SIZE = 188

# Simple wrapper around MPEG TS file
class MpegTSFile:
    def __init__(self, filename):
        self.fd = open(filename, "rb")

    # Find start of stream by looking for two consequtive TS packets
    def find_sync(self):
        while True:
            pos = self.fd.tell()

            x = self.fd.read(1)

            # Look for sync byte
            if x == '\x47':
                self.fd.seek(-1, 1)
                # Look for a second packet
                if self.read_packet()[0] == '\x47':
                    self.fd.seek(pos)
                    break
                else:
                    self.fd.seek(pos+1)

    def read_packet(self):
        return self.fd.read(TS_PACKET_SIZE)

    # Search for substring in file
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
                # Return containing packet
                pos = pos + buf_pos
                self.fd.seek(pos - (pos % 188))
                return self.read_packet()

    def seek(self, pos, whence=0):
        return self.fd.seek(pos, whence)

    def tell(self):
        return self.fd.tell()

class TSPacket:
    def __init__(self, data):
        self.data = data
        fd = cStringIO.StringIO(data)

        # TS header
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

        # Adaptation field
        if self.header["adap_field"]:
            length = ord(fd.read(1))
            flags = ord(fd.read(1))
            fd.read(length - 1)

        # Payload
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

# Find keyframes and return array of Frame objects
def get_keyframes(filename):
    fd = MpegTSFile(filename)

    fd.find_sync()

    keyframes = []

    last_keyframe = None

    while True:
        # Search for beginning of video frame
        data = fd.find("\x00\x00\x01\xe0")
        pos = fd.tell() - TS_PACKET_SIZE

        if data:
            packet = TSPacket(data)

            # Check if packet is start of a frame
            if (packet.header["payl_start"] and
                packet.header["cont_payl"] and
                packet.stream_id == '\xe0'):

                # Add duration to last keyframe, if set
                if last_keyframe:
                    last_keyframe.duration += 0.0417

                # Read another packet. keyframe start code is sometimes
                # in the next packet.
                data = fd.read_packet()

                if data:
                    next_packet = TSPacket(data)
                else:
                    next_packet = None

                keyframe = False

                for x in (packet, next_packet):
                    if not x:
                        continue

                    # Look for keyframe start code
                    if (x.payl.find("\x00\x00\x01\x67") != -1 or
                        x.payl.find("\x00\x00\x01\x06") != -1):
                        keyframe = True
                        break

                if keyframe:
                    # Look for start of next frame
                    if fd.find("\x00\x00\x01\xe0"):
                        # Include first packet of next frame in size
                        size = fd.tell() - pos
                        fd.seek(-TS_PACKET_SIZE, 1)
                    else:
                        size = fd.tell() - pos

                    frame = Frame(pos, size, keyframe, packet)

                    last_keyframe = frame
                    keyframes.append(frame)

        else:
            break

    return keyframes
