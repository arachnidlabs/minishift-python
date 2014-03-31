from minishift.font import font


class Interface(object):
    def send(self, data):
        raise NotImplementedError


class MCP2210Interface(Interface):
    def __init__(self, vid, pid):
        import mcp2210
        self.device = mcp2210.MCP2210(vid, pid)

    def send(self, data):
        print data.encode('hex')
        self.device.transfer(data)


class Canvas(object):
    def __init__(self, size=None):
        self.size = size
        self._wrap = False
        if size:
            self._data = [0] * size
        else:
            self._data = []

    @property
    def wrap(self):
        return self._wrap

    @wrap.setter
    def wrap(self, value):
        self._wrap = bool(value)

    def _getxy(self, idx):
        if isinstance(idx, tuple):
            x, y = idx
        else:
            x, y = idx, None

        if x >= len(self._data):
            if not self.size:
                self._data.extend([0] * (x - len(self._data) + 1))
            elif self._wrap:
                x %= self.size
            else:
                raise IndexError()
        elif x < 0:
            raise IndexError()

        if y is not None and (y < 0 or y >= 8):
            raise IndexError()

        return x, y

    def __getitem__(self, idx):
        x, y = self._getxy(idx)

        if y is None:
            return self._data[x]
        else:
            return (self._data[x] >> y) & 1

    def __setitem__(self, idx, value):
        x, y = self._getxy(idx)

        if y is None:
            self._data[x] = value
        elif value:
            self._data[x] |= 1 << y
        else:
            self._data[x] &= ~(1 << y)

    def write_text(self, x, text):
        for char in text:
            x = self.write_char(x, char)
            self[x] = 0
            x += 1
        return x

    def write_char(self, x, char):
        for col in font[ord(char)]:
            if char != ' ' and col == 0:
                continue
            self[x] = col
            x += 1
        return x

    def scroll(self):
        for x in range(len(self._data)):
            canvas = Canvas(1)
            canvas[0] = self[x]
            yield canvas

    def to_bytes(self):
        return ''.join(chr(x) for x in self._data)


class Minishift(object):
    def __init__(self, interface, width):
        self.interface = interface
        self.width = width
        self._canvas = Canvas(width)

    @property
    def canvas(self):
        return self._canvas

    @canvas.setter
    def canvas(self, canvas):
        self._canvas = canvas

    def update(self, canvas=None):
        if not canvas:
            canvas = self.canvas
        self.interface.send(canvas.to_bytes())
