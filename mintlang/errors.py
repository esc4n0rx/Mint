class MintError(Exception):
    pass

class LexerError(MintError):
    pass

class ParserError(MintError):
    pass

class LintError(MintError):
    pass

class RuntimeMintError(MintError):
    pass
