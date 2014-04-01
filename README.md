minishift-python
================

Python library for interfacing with the minishift.

## Installation

    >>> pip install minishift-python

or, to install from source:

    >>> git clone https://github.com/arachnidlabs/minishift-python.git
    >>> cd minishift-python
    >>> sudo setup.py install

## Usage

    >>> import minishift
    >>> width = 64
    >>> vid, pid = 0x04d8, 0xf517
    >>> ms = minishift.Minishift(minishift.MCP2210Interface(vid, pid), width)
    >>> ms.canvas.write_text(0, "Hello world")
    >>> ms.update()

you can also create your own canvas instead of using the built-in one:

    >>> canvas = minishift.Canvas(width)
    >>> x = canvas.write_text(0, "Test")
    >>> canvas[x, 0] = 1  # Set the bottom pixel on the line after the text to 1
    >>> ms.update(canvas)

and scrolling is supported with 'infinite' canvases that expand as needed:

    >>> canvas = minishift.Canvas()
    >>> canvas.write_text(0, "This is a message that's far too long for a display.")
    >>> for slice in canvas.scroll():
    >>>     ms.update(canvas)
    >>>     time.sleep(0.05)
