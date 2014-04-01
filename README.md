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

## HTTP Interface

The minishift module provides a daemon that exposes a simple HTTP interface for controlling a chain of minishifts. To run it:

    $ python -m minishift.minishiftd <width>

Where width is the width in pixels of your minishift chain. Run `python -m minishift.minishiftd --help` for command line arguments, which include `-d` to run as a daemon, and `-p` to bind to a specified host and port (the default is port 8000).

Once the daemon is running, you can make GET or POST requests to the `/set` URI to change what's displayed on the minishift. For example:

    $ curl -G http://localhost:8000/set --data-urlencode "text=Test!"

Displays "Test!" left-aligned on the minishift. To display scrolling text, specify the 'interval' parameter, in seconds per scroll step:

    $ curl -G http://localhost:8000/set --data-urlencode "text=To be or not to be, that is the question" -d "interval=0.05"

And to scroll something a specified number of times before clearing the display, specify the 'times' parameter:

    $ curl -G http://localhost:8000/set --data-urlencode "text=To be or not to be, that is the question" -d interval=0.05 -d times=2
