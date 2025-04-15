class CorrectorException(Exception): pass

class CorrectorSyntaxError(CorrectorException): pass

class CorrectorParserError(CorrectorException): pass
