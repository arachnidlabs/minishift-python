from minishift.font import font


class Interface(object):
    """An ABC for Minishift interfaces."""
    def send(self, data):
        """Sends data to the minishift."""
        raise NotImplementedError


class MCP2210Interface(Interface):
    """An interface implementation that communicates over the MCP2210 USB-SPI interface."""

    def __init__(self, vid=0x04d8, pid=0xf517):
        """Constructor.

        Arguments:
          vid: Integer. Vendor ID.
          pid: Integer. Product ID.
        """
        import mcp2210
        self.device = mcp2210.MCP2210(vid, pid)

    def send(self, data):
        self.device.transfer(data)


class Canvas(object):
    """Represents a canvas onto which images and text can be drawn.

    Canvases are assumed to be 8 pixels high.
    """

    def __init__(self, size=None):
        """Constructor.

        Arguments:
            size: integer. The width of the canvas. If not supplied, an 'infinite' canvas is
                created, which expands in size to accommodate whatever is written to it.
        """
        self.size = size
        self._wrap = False
        if size:
            self._data = [0] * size
        else:
            self._data = []

    @property
    def wrap(self):
        """Whether writes should wrap from the end of the display back to the beginning.

        Only valid for fixed-size canvases.
        """
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
        """Gets the value of a column or a single pixel from the canvas.

        >>> canvas[x]  # Returns a byte representing the specified column
        >>> canvas[x, y]  # Returns an integer representing the specified pixel
        """
        x, y = self._getxy(idx)

        if y is None:
            return self._data[x]
        else:
            return (self._data[x] >> y) & 1

    def __setitem__(self, idx, value):
        """Sets the value of a column or a single pixel on the canvas.

        >>> canvas[x] = value  # Sets a column
        >>> canvas[x, y] = 1  # Sets a pixel
        """
        x, y = self._getxy(idx)

        if y is None:
            self._data[x] = value
        elif value:
            self._data[x] |= 1 << y
        else:
            self._data[x] &= ~(1 << y)

    def write_text(self, x, text):
        """Writes a string of text to the canvas.

        Arguments:
            x: Start column
            text: Text to write

        Returns:
            The index of the first column after the text.
        """
        for char in text:
            x = self.write_char(x, char)
            self[x] = 0
            x += 1
        return x

    def write_char(self, x, char):
        """Writes a single character to the canvas.

        Arguments:
            x: Start column
            text: Character to write

        Returns:
            The index of the first column after the character.
        """
        for col in font[ord(char)]:
            if char != ' ' and col == 0:
                continue
            self[x] = col
            x += 1
        return x

    def scroll(self):
        """Returns an iterator that facilitates producing a scrolling display.

        Example:
            >>> for col in canvas.scroll():
            ...     minishift.update(col)
            ...     time.sleep(0.05)
        """
        for x in range(len(self._data)):
            canvas = Canvas(1)
            canvas[0] = self[x]
            yield canvas

    def to_bytes(self):
        """Returns a text representation of the canvas, suitable for sending to the minishift."""
        return ''.join(chr(x) for x in self._data)


class Minishift(object):
    """Interface for working with a chain of minishifts."""

    def __init__(self, interface, width):
        """Constructor.

        Arguments:
            interface: An instance of Interface for Minishift communication.
            width: The width of the Minishift array.
        """
        self.interface = interface
        self.width = width
        self._canvas = Canvas(width)

    @property
    def canvas(self):
        """The built-in canvas."""
        return self._canvas

    @canvas.setter
    def canvas(self, canvas):
        self._canvas = canvas

    def update(self, canvas=None):
        """Updates the minishift with a canvas image.

        Arguments:
            canvas: Optional. If supplied, draw the specified canvas to the minishift.
                Otherwise, draw the built-in canvas.
        """
        if not canvas:
            canvas = self.canvas
        self.interface.send(canvas.to_bytes())
