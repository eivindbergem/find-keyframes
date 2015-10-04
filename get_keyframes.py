from subprocess import Popen,PIPE
import json

def print_bytes(fd, b):
    while b > 0:
        print fd.read(2).encode("hex"),
        b -= 2

def print_bytes_str(s, b):
    pos = 0
    while b > 0:
    #for x in range(0, len(s), b):
        print s[pos:pos+2].encode("hex"),
        b -= 2
        pos += 2

#filename = "mystream-000001.ts"
#filename = "video.ts"
filename = "videoOnly0.ts"

p = Popen(["/Applications/ffprobe", "-v", "quiet", "-show_frames",
           "-select_streams", "v",
           "-of", "json", filename], stdout=PIPE)

stdout, stderr = p.communicate()

#stdout = open("frames.json").read()

data = json.loads(stdout)

fd = open(filename, "rb")

frames = 0
tt = 0.0
frame_list = []
for frame in data['frames']:
    if frame['key_frame'] in (1, ):
        #print frame['pkt_pos'], ": ",

        fd.seek(int(frame['pkt_pos']))
        #for i in range(0, 3):
        #    print '%02x' % int(fd.read(1))
        #x = fd.read(8)
        #print x.encode('hex'),

        #x = fd.read(8)
        #print x.encode('hex')

#        if float(frame['pkt_duration_time']) != 0.0417:
        #x = fd.read(64)
        #fd.seek(-64, 1)

#        if (x.find('\x00\x00\x01\x41') + x.find('\x00\x00\x01\x67') +
#            x.find('\x00\x00\x01\x01')) == -3:

        print_bytes(fd, 64)
#        print frame['key_frame']
        print frame['pkt_pos'],
        print frame['pkt_size']
        #print frame['pkt_duration_time'],
        #print frame['pkt_pts_time']
        frame_list.append(int(frame['pkt_pos']))
        tt += float(frame['pkt_duration_time'])
        frames += 1
        #print frame
        

print frames
print tt
fd.seek(0)

print

# while True:
#     b = fd.read(2)
#     if not b:
#         break

#     if b.encode('hex') == "0000":
#         b = fd.read(2).encode('hex')

#         if b == "0167":
#             fd.seek(fd.tell() - 4)
#             #print fd.tell() - 4, ":",
#             print_bytes(fd, 64)
#             print
#             #print fd.read(8).encode('hex'),
#             #print fd.read(8).encode('hex')

# print
#import mmap

# with open(filename, "r+b") as f:
#     mm = mmap.mmap(f.fileno(), 0)
#     while True:
#         pos = mm.find('\x00\x00\x01\x67\x64\x00')
#         if pos == -1:
#             break

#         mm.seek(pos)
#         print_bytes(mm, 32)
#         print

# buf = ""
# n = 0

# frame_list2 = []

# with open(filename, "rb") as fd:
#     blocksize = 1024*64

#     while True:
#         pos = buf.find('\x47\x41\x00')

#         if pos == -1 or len(buf) - pos < 64:
#             data = fd.read(blocksize)
#             if not data:
#                 break
#             buf += data
#         else:
#             if buf[pos+3] != '\x00':
#                 frame_list2.append(buf[pos+4:pos+6])
#                 n += 1

#             buf = buf[pos+2:]
            

# print "Num:", n

# print set(frame_list)
# print set(frame_list2)
# #print len(set(frame_list2) - set(frame_list))

class MpegTsFile:
    def __init__(self, filename):
        self.fd = open(filename, "rb")

    def find_sync(self):
        while True:
            pos = self.fd.tell()

            x = ord(self.fd.read(1))

            if x == 0x47:
                self.fd.seek(-1, 1)
                if ord(self.read_packet()[0]) == 0x47:
                    self.fd.seek(pos)
                    break
                else:
                    self.fd.seek(pos+1)

    def read_packet(self):
        return self.fd.read(188)

    def find(self, substr):
        pos = self.fd.tell()

        while True:
            packet = self.read_packet()
            #print self.fd.tell()
            
            if not packet:
                return ""

            if packet.find(substr) != -1:
                return packet

#        self.fd.seek(pos)
        return ""

    def seek(self, pos, whence=0):
        return self.fd.seek(pos, whence)

    def tell(self):
        return self.fd.tell()
                
class BufferedFile:
    blocksize = 348*188

    def __init__(self, fd):
        self.fd = fd
        self.pos = self.fd.tell()
        self.buf = ""

    def read(self, b):
        if b > len(self.buf):
            self.buf += self.fd.read(self.blocksize)

        s = self.buf[:b]
        self.buf = self.buf[b:]
        self.pos += len(s)

        return s

    def find(self, substr):
        orig_pos = self.fd.tell()
        
        while True:
            if not self.buf:
                return ""
            pos = self.buf.find(substr)
            if pos != -1:
                return self.fd.tell() + pos
            else:
                self.buf = self.fd.read(self.blocksize)

        

    def seek(self, pos, whence=0):
        if whence:
            if pos > 0 and len(self.buf) > pos:
                self.pos += pos
                self.buf = self.buf[pos:]
                return

            pos = self.pos + pos

        self.fd.seek(pos)
        self.pos = self.fd.tell()
        self.buf = ""

    def tell(self):
        return self.pos

import struct

import cStringIO

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
#            self.adap_field = {"discon": flags & 0x80,
#                               "random": flags & 0x40,
#                               "elemstreampri": flags & 0x20,
#                               "pcr": flags & 0x10,
#                               "opcr": flags & 0x8,
#                               "splicing": flags & 0x4,
#                               "private": flags & 0x2,
#                               "extension": flags & 0x1}

            fd.read(length - 1)

        if self.header['cont_payl']:
            self.stream_id = "\x00"

            self.start_code = fd.read(3)
            if self.start_code == '\x00\x00\x01':
                self.stream_id = fd.read(1)

                self.pes_length = struct.unpack('>H', fd.read(2))[0]

                flags = struct.unpack('>H', fd.read(2))[0]

 #               self.pes_header = {"marker": flags >> 14 & 0x2,
 #                                  "scrambling": flags >> 12 & 0x2,
 #                                  "priority": flags >> 11 & 0x1,
 #                                  "alignment": flags >> 10 & 0x1,
 #                                  "copyright": flags >> 9 & 0x1,
 #                                  "original": flags >> 8 & 0x1,
 #                                  "ptsdts": flags >> 6 & 0x2,
 #                                  "escr": flags >> 5 & 0x1,
 #                                  "es_rate": flags >> 4 & 0x1,
 #                                  "dsm": flags >> 3 & 0x1,
 #                                  "copy_info":	flags >> 2 & 0x1,
 #                                  "CRC": flags >> 1 & 0x1,
 #                                 "extension": flags & 0x1}
                fd.read(ord(fd.read(1)))

            self.payl = fd.read()

class Frame:
    def __init__(self, pos, size, is_keyframe, packet):
        self.pos = pos
        self.size = size
        self.is_keyframe = is_keyframe
        self.packet = packet

def get_ts_packets(filename):
    #fd = BufferedFile(open(filename, "rb"))
    fd = MpegTsFile(filename)

    fd.find_sync()

#    with open(filename, "rb") as fd:
    if True:
    #     header = '\x47'

    #     while True:
    #         x = fd.read(1)
    #         if x == header:
    #             pos = fd.tell()

    #             fd.seek(187, 1)
    #             x1 = fd.read(1)
    #             fd.seek(187, 1)
    #             x2 = fd.read(1)

    #             if x1 == header and x2 == header:
    #                 fd.seek(pos-1)
    #                 break
    #             else:
    #                 fd.seek(pos)

#        print "In sync"

        while True:
            data = fd.find("\x00\x00\x01\xe0")
            pos = fd.tell() - 188

            #data = fd.read(188)

            if data:
                packet = TSPacket(data)

                if (packet.header["payl_start"] and
                    packet.header["cont_payl"] and
                    packet.stream_id == '\xe0'):

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


                    #if packet.pes_length > 188:
                    #    fd.seek(pos +
                    #            (packet.pes_length - (packet.pes_length % 188)))
 #                   else:
 #                       fd.seek(pos + (0xffff - 111))
 #                   
                    if fd.find("\x00\x00\x01\xe0"):
                        size = fd.tell() - pos - 188*2
                        fd.seek(-188, 1)
                    else:
                        size = fd.tell() - pos

                    yield Frame(pos, size, keyframe, packet)

            else:
                break

import struct

frame_list2 = []

def get_frames(filename):
    frame_pos = 0
    n = 0

    packets = []
    for frame in get_ts_packets(filename):
        yield frame
        #if packet.data.find("\x00\x00\x01\x67") != -1:
            #print_bytes_str(packet.data, 64)
            #print
#            print packet.header



            #print hex(ord(packet.stream_id))

        # if (packet.header["payl_start"] and packet.header["cont_payl"] and
        #     packet.stream_id == '\xe0'):

        #     yield packet, pos

        #     packets = []

        #     frame_pos = pos
                
        # packets.append((packet, pos))

            #print_bytes_str(packet, 64)
            #print pos
            #frame_list2.append(pos)

            #for x in ("sync_byte", "tei", "payl_start", "tp", "pid", "scram",
            #          "adap", "cont_play", "contin"):
                #print header[x],
            #    print hex(int(header[x], 2)),

            #print

    print "Frames:", n

#        print "{0:b}".format(data)
        #print (hex(sync_byte), hex(tei), hex(payl_start), hex(tp), hex(pid),
        #       hex(scram), hex(adap), hex(cont_payl), hex(contin))

def get_keyframes(filename):
    n = 0
    frames = []

    for frame in get_frames(filename):
        #packet = frame[0][0]
        #pos = frame[0][1]

        #for x in frame:
#        if (framepacket.payl.find('\x00\x00\x01\x06') != -1 or
#            packet.payl.find('\x00\x00\x01\x67') != -1):
        if frame.is_keyframe:
            print_bytes_str(frame.packet.data, 64)
            print frame.pos, frame.size
            n += 1
            frame_list2.append(frame.pos)

            yield frame
            #break

                

    #     keyframe = frame[0].payl.find('\x00\x00\x01\x67') != -1

    #     if keyframe:
    #         n += 1

    #         if frame and frames[0]['keyframe']:
    #             yield {"pos": frames[0][1],
    #                    "size": len(frame),
    #                    "duration": 0.0417 * len(frames)}
    #             frame_list2.append(frames[0]['keyframe'])
    #         frames = []

    #     frames.append({"data": frame,
    #                    "pos": pos,
    #                    "keyframe": keyframe})

    # yield {"pos": frames[0]['pos'],
    #        "size": len(frames[0]['data']),
    #        "duration": 0.0417 * len(frames)}
    # frame_list2.append(frames[0]['keyframe'])

    print n

for x in get_keyframes(filename):
    pass

print set(frame_list2) ^ set(frame_list)

import sys

sys.exit(0)
# def get_frames(filename):
#     with open(filename, "rb") as fd:
#         blocksize = 1024*64
#         buf = ""
#         abs_pos = 0
#         header = '\x47'
# #        header = '\x00\x00\01\x09\xe0\x00\x00\x00\x01\x41'
# #        last_frame = ""

#         while True:
#             pos = buf.find(header, 2)
#  #           print abs_pos
# #            print fd.tell()
# #            print len(buf)
#             #print abs_pos

#             if pos == -1:
#                 data = fd.read(blocksize)
#                 if not data:
#                     break
#                 buf += data
#             else:
#                 #last_frame += buf[:pos]

#                 if buf.startswith(header):
#                     yield abs_pos, pos, buf[:pos]
#                     #last_frame = ""

#                 #last_frame = buf[pos:pos+4]
#                 abs_pos += pos
#                 buf = buf[pos:]

#print "Frames:"
#for pos, size, data in get_frames(filename):
#    print_bytes_str(data, 64)
#    print size

#frames = [x for x in get_frames(filename)]
#print len(frames)

# bitrate = 2583112

# x = 0

# frames = 0
# keyframes = []
# last_keyframe = None

# with open(filename, "rb") as fd:
#     blocksize = 1024*64
#     buf = ""
#     abs_pos = 0

#     while True:
# #        pos = buf.find('\x00\x00\x01\x09\xe0\x00\x00\x00\x01')
# #        pos = buf.find('\x00\x00\x01')
#         pos = buf.find('\x47\x40\x00')

#         #print fd.tell()
#         #print fd.tell()
#         #print pos
#         #print len(buf)
#         if pos == -1:
#             data = fd.read(blocksize)
#             if not data:
#                 break
#             buf += data
#         else:
            
#             abs_pos += pos
#             #buf = buf[pos:]

#             nal_type = buf[pos+3]

#             if nal_type in ('\x67', '\x41', '\x01'):
#                 if last_keyframe or nal_type == '\x67':
#                     frames += 1

#                 #if nal_type == '\x01' and buf[pos+4] not in ('\x9e', '\x9f'):
#                 #    print buf[pos:pos+32].encode("hex"),
#                 #    print abs_pos
#                     #print fd.tell() + pos - blocksize

#             if nal_type == '\x67':

#                 last_keyframe = {"pos": abs_pos,
#                                  "size": None,
#                                  "duration": 0.0417}
#                 keyframes.append(last_keyframe)
#             elif nal_type in ('\x41', '\x01'):
#                 if last_keyframe:
#                     if not last_keyframe['size']:
#                         last_keyframe['size'] = abs_pos - last_keyframe['pos']
#                     last_keyframe['duration'] += 0.0417

#             buf = buf[pos+4:]
#             abs_pos += 4

#print frames
#print keyframes

#print frames
#print sum([x['duration'] for x in keyframes])

from hls import Playlist

playlist = Playlist()
playlist.append_tags({"EXT-X-VERSION": 4,
                      "EXT-X-I-FRAMES-ONLY": None})

duration = 0
for frame in get_keyframes(filename):
    duration += frame['duration']
    playlist.append_tag("EXTINF", "%f," % frame['duration'])
    playlist.append_tag("EXT-X-BYTERANGE", "%d@%d" % (frame['size'] + 188,
                                                      frame['pos']))
    playlist.append(filename)

playlist.append_tag("EXT-X-ENDLIST")

playlist.write("iframe_index.m3u8")

print duration

#        pos = fd.tell()
#        buf = fd.read(blocksize)
#        if not s:
#            break

        #pos2 = s.find('\x00\x00\x01\x67\x64\x00')
#        pos2 = s.find('\x00\x00\x01\x65\x88')

#        pos2 = s.find('\x47\xa2\xed\x19')
        #pos2 = s.find('\x3d\x2a\xcd\x9f')
        
#        if pos2 != -1:
#            x += 1
#            fd.seek(pos + pos2)
#            print_bytes(fd, 64)
#            print fd.tell()
            #fd.seek(bitrate, 1)
            #print

#print x
