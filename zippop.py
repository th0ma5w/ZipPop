#!/usr/bin/env python3
import os, struct, zipfile
from pprint import pprint
from pathlib import Path

EOCD     = '<IhhhhIIh'
EOCD_loc = '<IIQI'
EOCD64h  = '<IQ' 
EOCD64a  = 'hhIIQQQQ'
EOCD64ha = EOCD64h + EOCD64a
EOCD64c  = '{}s'
CD       = '<IhhhhhhIIIhhhhhII'
CDX      = '{}s{}s{}s'
LFH      = '<IhhhhhIIIhh'
LFHX     = '<{}s{}s'

EOCD_SIZE      = struct.calcsize(EOCD)
EOCD_loc_SIZE  = struct.calcsize(EOCD_loc)
EOCD64h_SIZE   = struct.calcsize(EOCD64h)
EOCD64ha_SIZE  = struct.calcsize(EOCD64ha)
CD_SIZE        = struct.calcsize(CD)
LFH_SIZE       = struct.calcsize(LFH)

EOCD_header = """
Signature
Disk Number
CD Disk
CD Count
CD Records
CD Size
CD Offset
Comment Length
""".strip().splitlines()

EOCD64_header = """
Signature
Dir Size
Version
Min Version
Disk Number
CD Disk
CD Count
CD Records
CD Size
CD Offset
Comment
""".strip().splitlines()

EOCD_loc_header = """
Signature
Start Disk
Offset
Disk Count
""".strip().splitlines()

CD_header ="""
Signature
Version
Min Version
Bit Flag
Method
Time
Date
CRC
Compressed
Uncompressed
Name Length
Extra Length
Comment Length
Start Disk
Internal
External
LFH Offset
""".strip().splitlines()

CDX_header = """
Name
Extra
Comment
""".strip().splitlines()

CDFH_header = CD_header + CDX_header

LFH_header="""
Signature
Min Version
Bit Flag
Method
Time
Date
CRC
Compressed
Uncompressed
Name Length
Extra length
""".strip().splitlines()

LFHX_header="""
ID
Length
""".strip().splitlines()

class Entry:
    pass

class my_zip:
    def __init__(self, filename):
        self.f = open(filename,'rb')
        self.sixtyfour = False
        self.entries=[]
        self.addresses = []
        self.filename = filename
        self.filesize = os.path.getsize(filename)
        self.addresses.append([self.filesize, 'zip', '00_end'])
        self.find_eocd()
        #try:
        #    self.find_eocd()
        #except:
        #    pass
    def find_eocd64(self):
        self.f.seek(self.eocd64_offset)
        self.eocd64h = self.f.read(EOCD64h_SIZE)
        self.EOCD64h = struct.unpack(EOCD64h, self.eocd64h)
        self.eocd64ac_size = self.EOCD64h[1]
        self.eocd64_size = EOCD64h_SIZE + self.eocd64ac_size
        self.addresses.append([
            self.eocd64_offset + self.eocd64_size
            , 'zip64', 
            '09_eocd64_e'])
        self.eocd64ac = self.f.read(self.eocd64ac_size)
        self.eocd64 = self.eocd64h + self.eocd64ac
        self.eocd64c_size = self.eocd64_size - EOCD64ha_SIZE
        self.eocd64c_s = EOCD64ha + EOCD64c.format(self.eocd64c_size)
        self.EOCD64 = struct.unpack(
                self.eocd64c_s,
                self.eocd64)
        self.cd_length = self.EOCD64[8]
        self.cd_offset = self.EOCD64[9]
        self.cd_end    = self.cd_offset + self.cd_length
        self.addresses.append([self.cd_offset, 'zip64', '04_cd_offset'])
        self.addresses.append([self.cd_end, 'zip', '05_cd_end'])
        self.find_cd()
    def find_eocd_locator(self):
        self.sixtyfour = True
        eocd64_loc_start = self.eocd_search.rfind(
                0x07064b50.to_bytes(4,'little'))
        self.addresses.append([
            self.seek_pos + eocd64_loc_start, 'zip64', '10_loc_offset'])
        self.eocd_loc_offset = self.seek_pos + eocd64_loc_start
        self.eocd_loc = self.eocd_search[eocd64_loc_start:][:EOCD_loc_SIZE]
        self.EOCD_loc = struct.unpack(EOCD_loc, self.eocd_loc)
        self.eocd64_offset = self.EOCD_loc[2]
        self.addresses.append([
            self.eocd64_offset, 'zip64', '08_eocd64_b'])
        self.find_eocd64()
    def find_eocd(self):
        seek_to = 0 - self.filesize
        if seek_to < -65557:
            seek_to = -65557
        self.f.seek(seek_to,2)
        self.seek_to = seek_to
        self.seek_pos = self.filesize + seek_to
        self.addresses.append([self.seek_pos, 'zip', '01_seek'])
        self.eocd_search = self.f.read()
        eocd_start = self.eocd_search.rfind(
                0x06054b50.to_bytes(4,'little'))
        b = eocd_start
        e = eocd_start + EOCD_SIZE
        self.addresses.append([self.seek_pos + b, 'zip', '02_eoc_b'])
        self.addresses.append([self.seek_pos + e, 'zip', '03_eoc_e'])
        self.eocd_offset = self.seek_pos + b
        self.eocd = self.eocd_search[b:e]
        self.EOCD = struct.unpack(EOCD,self.eocd)
        self.cd_length = self.EOCD[5]
        self.cd_offset = self.EOCD[6]
        self.cd_end    = self.cd_offset + self.cd_length
        self.addresses.append([self.cd_offset, 'zip', '04_cd_offset'])
        self.addresses.append([self.cd_end, 'zip', '05_cd_end'])
        if self.EOCD[6] == 0xffffffff:
            self.find_eocd_locator()
        else:
            self.find_cd()
    def find_cd(self):
        c=0
        self.cd_parse_offset = 0
        while self.find_cd_file():
            #print(c,end=" ")
            c += 1
    def find_cd_file(self):
        self.addresses.append(
                [self.cd_offset + self.cd_parse_offset, 
                 'zip', '12_cd_entry_offset'])
        self.f.seek(self.cd_offset + self.cd_parse_offset)
        a=Entry()
        self.entries.append(a)
        a.cd_offset = self.cd_offset + self.cd_parse_offset
        a.cd = self.f.read(CD_SIZE)
        a.CD = struct.unpack(CD, a.cd)
        a.cdx_s = CDX.format(a.CD[10],a.CD[11],a.CD[12])
        CDFH = CD + a.cdx_s
        size_remaining = sum([a.CD[10],a.CD[11],a.CD[12]])
        a.cdx = self.f.read(size_remaining)
        a.cdfh = a.cd + a.cdx
        a.cdfh_size = struct.calcsize(CDFH)
        a.cd_end = self.cd_offset + self.cd_parse_offset + a.cdfh_size
        a.CDFH = struct.unpack(CDFH, a.cdfh)
        self.cd_parse_offset += a.cdfh_size
        a.val_lookup = {
                'unc_size'  : a.CDFH[8],
                'comp_size' : a.CDFH[9],
                'lh_offset' : a.CDFH[16],
                'disk_no'   : a.CDFH[13]
                }
        a.ext_truth = [
                ['unc_size',   a.CDFH[8]  == 0xffffffff, 'Q', 8, 0],
                ['comp_size',  a.CDFH[9]  == 0xffffffff, 'Q', 8, 0],
                ['lh_offset',  a.CDFH[16] == 0xffffffff, 'Q', 8, 0],
                ['disk_no',    a.CDFH[13] == 0xff, 'I', 4, 0]
                ]
        if True in [x[1] for x in a.ext_truth]:
            a.EXTh = '<hh'
            a.EXTh_SIZE = struct.calcsize(a.EXTh)
            a.cdfh_ext  = a.CDFH[18]
            a.cdfh_exth = a.cdfh_ext[:a.EXTh_SIZE]
            a.CDFH_exth = struct.unpack(a.EXTh, a.cdfh_exth)
            a.cdfh_ext_chunk_size = a.CDFH_exth[1]
            a.truthy_chunk_size = sum([x[3] for x in a.ext_truth if x[1]])
            a.EXT = a.EXTh + ''.join([x[2] for x in a.ext_truth if x[1]])
            a.EXT_SIZE = struct.calcsize(a.EXT)
            a.CDFH_ext = struct.unpack(a.EXT, a.cdfh_ext[0-a.EXT_SIZE:])
            a.ext_true_only = [x for x in a.ext_truth if x[1]]
            a.ext_processed = zip(a.ext_true_only, a.CDFH_ext[2:])
            [a.val_lookup.update(
                {
                x[0][0]:x[1]
                }) 
             for x in a.ext_processed]
        self.find_local_header(a)
        if self.cd_parse_offset < self.cd_length:
            return True
        else:
            return False
    def find_local_header(self,e):
        lh_offset = e.val_lookup['lh_offset']
        comp_size = e.val_lookup['comp_size']
        e.filename = e.CDFH[17].decode('utf-8')
        self.addresses.append([lh_offset, e.filename, '06_lfh_s'])
        self.f.seek(lh_offset)
        self.lh_offset = lh_offset
        self.parse_local_header(e)
    def parse_local_header(self, e):
        e.lfh = self.f.read(LFH_SIZE)
        e.LFH = struct.unpack(LFH, e.lfh)
        e.lfhx_s = LFHX.format(e.LFH[9],e.LFH[10])
        e.total_length = e.LFH[7]
        e.compression = e.LFH[3]
        e.total_lfh_length = sum([LFH_SIZE, e.LFH[9], e.LFH[10]])
        e.data_offset = self.lh_offset + e.total_lfh_length
        e.data_end = e.data_offset+e.total_length
        self.addresses.append([e.data_offset, e.filename, '07_data_b'])
        self.addresses.append([e.data_end, e.filename, '07_data_e'])
        e.lfhx_l = struct.calcsize(e.lfhx_s)
        e.lfhx = self.f.read(e.lfhx_l)
        e.LFHX = struct.unpack(e.lfhx_s, e.lfhx)
    def pop_last_analysis(self):
        pass
    def pop_last_64(self):
        #newcd
        self.f.seek(self.cd_offset)
        self.new_cd = self.f.read(self.entries[-1].cd_offset - self.cd_offset)
        #oldend
        self.f.seek(self.cd_offset)
        self.old_end = self.f.read()
        #rest
        self.f.seek(self.entries[-1].cd_end)
        self.rest = self.f.read()
        #combine
        self.new_cd_size = len(self.new_cd)
        self.truncate_to = self.entries[-1].val_lookup['lh_offset']
        new_EOCD = list(self.EOCD)
        new_EOCD[3] -= 1
        new_EOCD[4] -= 1
        new_EOCD[5]  = self.new_cd_size
        new_EOCD_loc = list(self.EOCD_loc)
        new_EOCD_loc[2]  = self.truncate_to + self.new_cd_size
        new_EOCD64 = list(self.EOCD64)
        new_EOCD64[6] -= 1
        new_EOCD64[7] -= 1
        new_EOCD64[8] = self.new_cd_size
        new_EOCD64[9] = self.truncate_to
        self.new_rest = b''.join([
            self.synth_eocd64(new_EOCD64),
            self.synth_eocd_loc(new_EOCD_loc),
            self.synth_eocd(new_EOCD)
            ])
        self.new_end = self.new_cd + self.new_rest
        #pprint([
        #    self.old_end,
        #    self.new_end,
        #    self.new_cd_size,
        #    self.filesize,
        #    self.truncate_to
        #    ])
        self.do_pop()
    def pop_last_non_64(self):
        #newcd
        self.f.seek(self.cd_offset)
        self.new_cd = self.f.read(self.entries[-1].cd_offset - self.cd_offset)
        #oldend
        self.f.seek(self.cd_offset)
        self.old_end = self.f.read()
        #rest
        self.f.seek(self.entries[-1].cd_end)
        self.rest = self.f.read()
        #combine
        self.new_cd_size = len(self.new_cd)
        self.truncate_to = self.entries[-1].val_lookup['lh_offset']
        new_EOCD = list(self.EOCD)
        new_EOCD[3] -= 1
        new_EOCD[4] -= 1
        new_EOCD[5]  = self.new_cd_size
        new_EOCD[6]  = self.truncate_to
        self.new_EOCD=new_EOCD
        self.new_end = self.new_cd + self.synth_eocd(new_EOCD)
        #pprint([
        #    self.old_end,
        #    self.new_end,
        #    self.new_cd_size,
        #    self.filesize,
        #    self.truncate_to
        #    ])
        self.do_pop()
    def do_pop(self):
        print("Popping zip: " + self.filename)
        self.do_export()
        self.do_truncate()
    def do_export(self):
        last = self.entries[-1]
        Path(last.filename).parent.mkdir(parents=True, exist_ok=True)
        if not last.filename[-1]=='/':
            print('writing out: ' + last.filename)
            self.gg = open(last.filename,'wb')
            self.f.seek(last.data_offset)
            decompressor = zipfile._get_decompressor(last.compression)
            if decompressor is not None:
                self.gg.write(
                        decompressor.decompress(
                            self.f.read(last.total_length)
                            )
                        )
            else:
                self.gg.write(self.f.read(last.total_length))
            self.gg.close()
        else:
            print('skipping_dir: ' + last.filename)
    def do_truncate(self):
        print('shrinking zip: ' + self.filename)
        print('old size: ' + str(self.filesize))
        print('new size: ' + str(self.truncate_to))
        self.f = open(self.filename,'ab')
        self.f.seek(self.truncate_to)
        self.f.truncate()
        self.f.write(self.new_end)
        self.f.close()
        print('done.')
    def entry_location_analysis(self):
        return [
                [
                    e.CDX[0],
                    e.CD[-1],
                    LFH_SIZE,
                    e.total_lfh_length,
                    e.data_offset,
                    e.total_length
                ]
                for e in self.entries
                ]
    def dump_info(self):
        j = lambda x,y : dict(zip(x,y))
        self.info = {
                'eocd'  : j(EOCD_header, self.EOCD),
                'entries' : [
                    {
                        'cd'   : j(CD_header, e.CD),
                        'cdx'  : j(CDX_header, e.CDX),
                        'lfh'  : j(LFH_header, e.LFH)
                    }
                    for e in self.entries
                    ]
                }
        return self.info
    def synth_eocd(self, eocd):
        return struct.pack(EOCD, *eocd)
    def synth_eocd64(self, eocd64):
        return struct.pack(self.eocd64c_s, *eocd64)
    def synth_eocd_loc(self, eocd_loc):
        return struct.pack(EOCD_loc, *eocd_loc)
    def synth_cd(self, cd):
        return struct.pack(CD, *cd)
    def pop_last(self):
        if self.sixtyfour:
            self.pop_last_64()
        else:
            self.pop_last_non_64()



import sys

command, filename = sys.argv[1:3]

if command == "pop":
    z = my_zip(filename)
    z.pop_last()

if command == "all":
    z = my_zip(filename)
    for x in range(len(z.entries)):
        z = my_zip(filename)
        z.pop_last()

