class CorrectorException(Exception): pass

class CorrectorSyntaxError(CorrectorException): pass

class CorrectorCannotError(CorrectorException): pass

class CorrectorMemoryError(CorrectorException): pass
