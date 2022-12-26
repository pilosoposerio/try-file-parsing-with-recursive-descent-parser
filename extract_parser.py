from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Optional

from extract_lexer import ExtractLexer, ExtractToken, ExtractTokenType
from transcript_lexer import TranscriptLexer
from transcript_parser import TranscriptParser
from segment_emitter import SegmentEmitter


@dataclass
class ExtractParser:
    lexer: ExtractLexer
    emitter: SegmentEmitter

    current_token: Optional[ExtractToken] = field(default=None, init=False)
    peek_token: Optional[ExtractToken] = field(default=None, init=False)
    tokens: Generator[Optional[ExtractToken], None, None] = field(init=False)

    def __post_init__(self):
        self.tokens = self.lexer.get_tokens()
        self.consume_token()
        self.consume_token()

    def consume_token(self) -> str:
        token: ExtractToken = ExtractToken.NONE
        temp: ExtractToken = self.current_token
        try:
            token = next(self.tokens)
        except StopIteration:
            pass
        finally:
            self.current_token = self.peek_token
            self.peek_token = token

        if temp:
            return temp.text
        return ""

    def check_current_token(self, kind: ExtractTokenType) -> bool:
        return self.current_token.type == kind

    def check_peek_token(self, kind: ExtractTokenType) -> bool:
        return self.peek_token.type == kind

    def match(self, kind: ExtractTokenType) -> str:
        """
        consume a token of type `kind`

        errors if type does not match
        """
        assert self.check_current_token(kind), (f"Expecting a {kind}, got "
                                                f"{self.current_token.type}")
        return self.consume_token()

    def parse(self):
        """
        extract ::= {utterance}
        """
        while not self.check_current_token(ExtractTokenType.EOF):
            self.parse_utterance()

    def parse_utterance(self):
        """
        utterance ::= {metadata} nl
        """
        while self.current_token.type not in (ExtractTokenType.NEWLINE,
                                              ExtractTokenType.EOF):
            self.parse_metadata()
        if self.check_current_token(ExtractTokenType.NEWLINE):
            self.parse_newline()

    def _is_current_token_generic_meta_key(self):
        return (
            self.check_current_token(ExtractTokenType.FILE_META_KEY)
            or self.check_current_token(ExtractTokenType.HYPOTHESIS_META_KEY)
            or self.check_current_token(ExtractTokenType.LABELS_META_KEY)
            or self.check_current_token(ExtractTokenType.USER_META_KEY)
        )

    def parse_optional_string(self) -> str:
        """
        consume current token if it is a string
        """
        value: str = ""
        if self.check_current_token(ExtractTokenType.STRING):
            # optional, value might be empty
            value = self.parse_string()

        return value

    def parse_metadata(self):
        """
        metadata::= {
            filemeta
            |intervalmeta
            |transcriptionmeta
            |hypothesismeta
            |labelsmeta
            |usermeta}
        """
        if self._is_current_token_generic_meta_key():
            meta_key: str = self.consume_token()

            value: str = self.parse_optional_string()
            self.emitter.set_meta_key(meta_key, value)

        elif self.check_current_token(ExtractTokenType.INTERVAL_META_KEY):
            self.consume_token()
            self.parse_interval()
        elif self.check_current_token(ExtractTokenType.TRANSCRIPTION_META_KEY):
            self.consume_token()
            self.parse_transcription()
        else:
            raise ValueError(
                f"Expecting '*_META_KEY', got {self.current_token}"
            )

        self.parse_newline()

    def parse_string(self) -> str:
        return self.match(ExtractTokenType.STRING)

    def parse_interval(self):
        interval_start: int = self.parse_timestamp()
        self.parse_whitespace()
        interval_end: int = self.parse_timestamp()

        self.emitter.set_interval_start(interval_start)
        self.emitter.set_interval_end(interval_end)

    def parse_newline(self):
        return self.match(ExtractTokenType.NEWLINE)

    def parse_timestamp(self) -> int:
        iso_format_time: str = self.match(ExtractTokenType.TIMESTAMP)
        # TODO how to typehint this?
        hours, minutes, seconds = iso_format_time.split(":")
        hours, minutes, seconds = int(hours), int(minutes), float(seconds)

        # convert time to milliseconds
        milliseconds: int = 0

        minutes += (hours * 60)
        seconds += (minutes * 60)
        milliseconds += int(seconds * 1000)

        return milliseconds

    def parse_whitespace(self):
        value: str = ""
        while self.check_current_token(ExtractTokenType.WHITESPACE):
            value = f"{value}{self.match(ExtractTokenType.WHITESPACE)}"

    def parse_transcription(self):
        """
        tx ::=
        """
        transcript: str = self.match(ExtractTokenType.STRING)
        transcript_lexer: TranscriptLexer = TranscriptLexer(transcript)
        transcript_parser: TranscriptParser = TranscriptParser(
            transcript_lexer, self.emitter)
        transcript_parser.parse()
