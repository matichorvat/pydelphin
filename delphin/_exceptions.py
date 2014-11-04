
class PyDelphinException(Exception):
    pass


class ItsdbError(PyDelphinException):
    pass


class XmrsError(PyDelphinException):
    pass


class XmrsSerializationError(XmrsError):
    pass


class XmrsDeserializationError(XmrsError):
    pass


class XmrsStructureError(XmrsError):
    pass

class TdlError(PyDelphinException):
    pass

class TdlParsingError(TdlError):
    def __init__(self, *args,
                 **kwargs):
        if 'identifier' in kwargs: identifier = kwargs['identifier']; del kwargs['identifier']
        else: identifier = None
        if 'line_number' in kwargs: line_number = kwargs['line_number']; del kwargs['line_number']
        else: line_number = None
        if 'filename' in kwargs: filename = kwargs['filename']; del kwargs['filename']
        else: filename = None
        TdlError.__init__(self, *args, **kwargs)
        self.filename = filename
        self.line_number = line_number
        self.identifier = identifier

    def __str__(self):
        return u'At {}:{} ({})\n{}'.format(
            self.filename or u'?',
            self.line_number or u'?',
            self.identifier or u'type/rule definition',
            TdlError.__str__(self)
        )
