# -*- coding:gbk -*-

import struct

class CQUnpack(object):
    def __init__(self, data):
        self._data      = data
        self._length    = len(data)
        self._location  = 0

    def _Get_(self, fmt, len):
        ret = struct.unpack(fmt, self._data[self._location:self._location + len])[0]
        self._location += len
        return ret

    def GetByte(self):
        return self._Get_('B', 1)

    def GetShort(self):
        return self._Get_('!H', 2)

    def GetInt(self):
        return self._Get_('!I', 4)

    def GetLong(self):
        return self._Get_('!Q', 8)

    def GetLenStr(self):
        len = self.GetShort()
        ret = self._data[self._location:self._location + len]
        self._location += len
        return ret
