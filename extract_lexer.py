import re

from dataclasses import dataclass
from enum import Enum, unique, auto
from pathlib import Path
from typing import Final


@unique
class ExtractTokenType(Enum):

    # constants
    EOF = 0

    # keywords
    # `FILE: ` at the beginning of a line
    FILE_META_KEY = auto()

    # `INTERVAL: ` at the beginning of a line
    INTERVAL_META_KEY = auto()

    # `TRANSCRIPTION: ` at the beginning of a line
    TRANSCRIPTION_META_KEY = auto()

    # `HYPOTHESIS: ` at the beginning of a line
    HYPOTHESIS_META_KEY = auto()

    # `LABELS: ` at the beginning of a line
    LABELS_META_KEY = auto()

    # `USERS: ` at the beginning of a line
    USER_META_KEY = auto()

    # values
    TIMESTAMP = auto()
    NEWLINE = auto()
    WHITESPACE = auto()
    STRING = auto()


@dataclass
class ExtractToken:
    """
    token from extract.txt
    """

    text: str
    type: ExtractTokenType


ExtractToken.NONE: Final[ExtractToken] = ExtractToken(None, None)


@dataclass
class ExtractLexeme:
    """
    data structure to store one lexeme
    """

    token_type: ExtractTokenType
    pattern: str

    @property
    def name(self):
        return self.token_type.name


class ExtractLexer:
    """
    class for get tokens of extract.txt
    """

    LEXEMES: Final[list[ExtractLexeme]] = [
        ExtractLexeme(ExtractTokenType.FILE_META_KEY, r"^FILE: ?"),
        ExtractLexeme(ExtractTokenType.INTERVAL_META_KEY, r"^INTERVAL: ?"),
        ExtractLexeme(ExtractTokenType.TRANSCRIPTION_META_KEY,
                      r"^TRANSCRIPTION: ?"),
        ExtractLexeme(ExtractTokenType.HYPOTHESIS_META_KEY, r"^HYPOTHESIS: ?"),
        ExtractLexeme(ExtractTokenType.LABELS_META_KEY, r"^LABELS: ?"),
        ExtractLexeme(ExtractTokenType.USER_META_KEY, r"^USER: ?"),
        ExtractLexeme(ExtractTokenType.TIMESTAMP,
                      r"\b\d+:\d{1,2}:\d{1,2}\.\d{3}\b"),
        ExtractLexeme(ExtractTokenType.NEWLINE, "\n"),
        ExtractLexeme(ExtractTokenType.WHITESPACE, r"[ \t]+"),
        ExtractLexeme(ExtractTokenType.STRING, r".+"),
    ]

    @classmethod
    def build_lexeme_regex(cls):
        # create named pattern groups
        patterns: list[str] = ["(?P<%s>%s)" % (lexeme.name, lexeme.pattern)
                               for lexeme in cls.LEXEMES]
        singularity: str = '|'.join(patterns)

        return singularity

    def __init__(self, input_file_path: str):
        self.source: Path = Path(input_file_path)

    def get_tokens(self) -> ExtractToken:
        """
        token generator
        """
        pattern: re.Pattern = re.compile(ExtractLexer.build_lexeme_regex())

        with open(self.source) as fh:
            for line in fh:
                for match in pattern.finditer(line):
                    token_type = match.lastgroup
                    value = match.group()

                    yield(ExtractToken(value, ExtractTokenType[token_type]))

            yield ExtractToken("", ExtractTokenType.EOF)
