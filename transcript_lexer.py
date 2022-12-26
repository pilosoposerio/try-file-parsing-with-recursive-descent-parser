import re

from dataclasses import dataclass
from enum import Enum, unique, auto
from typing import Final


@unique
class TranscriptTokenType(Enum):

    SPEAKER = auto()
    TIMESTAMP = auto()
    TILDE = auto()
    WHITESPACE = auto()
    SOUNDTAG = auto()
    STRING = auto()
    UNKNOWN = auto()


@dataclass
class TranscriptToken:
    """
    token from extract.txt transcription values
    """

    text: str
    type: TranscriptTokenType


TranscriptToken.NONE = TranscriptToken(None, None)


@dataclass
class TranscriptLexeme:
    """
    data structure to store one lexeme
    """

    token_type: TranscriptTokenType
    pattern: str

    @property
    def name(self):
        return self.token_type.name


class TranscriptLexer:
    """
    class for get tokens of extract.txt
    """

    LEXEMES: Final[list[TranscriptLexeme]] = [
        TranscriptLexeme(TranscriptTokenType.SPEAKER,
                         r"<#[0-9A-Za-z_-]+>"),
        TranscriptLexeme(TranscriptTokenType.SOUNDTAG,
                         r"<(?P<tag>[a-z]+)>([a-z]+</(?P=tag)>)?"),
        TranscriptLexeme(TranscriptTokenType.TILDE, r"~$"),
        TranscriptLexeme(TranscriptTokenType.TIMESTAMP,
                         r"\[(\d+(\.\d*)?)\]"),
        TranscriptLexeme(TranscriptTokenType.WHITESPACE,
                         r"[ \t]+"),
        TranscriptLexeme(TranscriptTokenType.UNKNOWN,
                         r"."),
    ]

    @classmethod
    def build_lexeme_regex(cls):
        # create named pattern groups
        patterns: list[str] = ["(?P<%s>%s)" % (lexeme.name, lexeme.pattern)
                               for lexeme in cls.LEXEMES]
        singularity: str = '|'.join(patterns)

        return singularity

    def __init__(self, input_string: str):
        self.source: str = input_string

    def get_tokens(self):
        """
        token generator
        """
        for token in TranscriptLexer.tokenize(self.source):
            yield token

    @staticmethod
    def tokenize(input_string: str):
        pattern: re.Pattern = re.compile(TranscriptLexer.build_lexeme_regex())

        for match in pattern.finditer(input_string):
            token_type = match.lastgroup
            value = match.group()

            yield(TranscriptToken(value, TranscriptTokenType[token_type]))
