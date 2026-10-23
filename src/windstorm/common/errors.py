"""windstorm exception types.

Library-callable error contract (issue #96): windstorm's internal lookup paths
must NOT abort the process. Rikki's sensor-verification pipeline drives
windstorm programmatically and needs a missing element / missing variable to be
a catchable, data-level ``UNVERIFIABLE`` — not a ``sys.exit()``. All library
lookups raise :class:`WindstormLookupError`; only the CLI boundary
(``main.windstorm`` entrypoint) turns it into a clean exit.
"""


class WindstormLookupError(KeyError):
    """Raised when a requested model element, marker, or template key is missing.

    Subclasses ``KeyError`` so existing ``except KeyError`` handlers keep
    working, but is catchable as a *data-level* error — a caller can trap it,
    record it as evidence (e.g. ``UNVERIFIABLE`` per requirement), and continue
    the run instead of aborting the process.
    """

    def __str__(self) -> str:
        # KeyError.__str__ returns repr(args[0]) (quote-wrapped); a lookup error
        # reads better and is friendlier to ``record["detail"] = str(e)``
        # without the surrounding quotes.
        return str(self.args[0]) if self.args else ""
