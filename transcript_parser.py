from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Optional

from segment_emitter import SegmentEmitter
from transcript_lexer import (
    TranscriptLexer,
    TranscriptToken,
    TranscriptTokenType
)


@dataclass
class TranscriptParser:
    lexer: TranscriptLexer
    emitter: SegmentEmitter

    current_token: Optional[TranscriptToken] = field(default=None, init=False)
    peek_token: Optional[TranscriptToken] = field(default=None, init=False)
    tokens: Generator[TranscriptToken, None, None] = field(init=False)

    def __post_init__(self):
        self.tokens = self.lexer.get_tokens()
        self.consume_token()
        self.consume_token()

    def consume_token(self):
        token: TranscriptToken = TranscriptToken.NONE
        temp: TranscriptToken = self.current_token
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

    def check_current_token(self, kind: TranscriptTokenType):
        return self.current_token.type == kind

    def check_peek_token(self, kind: TranscriptTokenType):
        return self.peek_token.type == kind

    def match(self, kind: TranscriptTokenType):
        """
        consume a token of type `kind`

        errors if type does not match
        """
        assert self.check_current_token(kind), (f"Expecting a {kind}, got "
                                                f"{self.current_token.type}")
        return self.consume_token()

    def parse(self):
        """
        call parse_transcript
        """
        self.parse_transcript()
        assert self.current_token == TranscriptToken.NONE, (
            "Expecting that all tokens have been consumed... "
            f"but there seems to be some left: {self.current_token.type}"
        )

    def parse_transcript(self):
        """
        transcript ::= message|segment [{timestamp segment}] [tilde]

        transcript starts with a `message` if the utterance is a continuation
        of the previous utterance
        """
        if not self.emitter.is_merge_next:
            self.emitter.use_default_segment_start()
            # self.parse_head_transcript()
            self.parse_segment()
        else:
            self.emitter.unset_merge_next()
            message: str = self.parse_message()
            self.emitter.append_message(message)

        while self.check_current_token(TranscriptTokenType.TIMESTAMP):
            time_offset: int = self.parse_timestamp()
            end: int = self.emitter.compute_segment_end(time_offset)
            self.emitter.set_segment_end(end)
            self.emitter.emit()

            # prep for next segment
            self.emitter.set_segment_start(end)

            self.parse_segment()

        if self.check_current_token(TranscriptTokenType.TILDE):
            # last segment in utterance is broken
            # i.e. needs to merge to next utterance
            self.consume_token()
            self.emitter.set_merge_next()
        else:
            # last segment in utterance uses interval end as its end
            self.emitter.use_default_segment_end()
            self.emitter.emit()

    def parse_segment(self):
        """
        segment ::= speaker message
        """

        # cleanup leading whitespaces
        self.ignore_whitespaces()

        speaker: str = ""
        message: str = ""

        if self.check_current_token(TranscriptTokenType.SPEAKER):
            speaker = self.parse_speaker()
            if speaker != "no-speech":
                message = self.parse_message()
                self.emitter.set_message(message)
            else:
                speaker = ""
        elif self.check_current_token(TranscriptTokenType.SOUNDTAG):
            message = self.consume_token()
        else:
            raise ValueError(("Expecting segment tokens, got"
                              f" {self.current_token.type}"))

        # override speaker and message
        self.emitter.set_speaker(speaker)
        self.emitter.set_message(message)

        # cleanup trailing whitespaces
        self.ignore_whitespaces()

        return speaker, message

    def parse_timestamp(self) -> int:
        """
        timestamp ::= "[SS.fff]"

        returns in milliseconds
        """
        time_offset: str = self.match(TranscriptTokenType.TIMESTAMP)
        seconds: str = time_offset[1:-1]
        milliseconds = int(float(seconds) * 1000)
        return milliseconds

    def parse_speaker(self):
        speaker: str = self.match(TranscriptTokenType.SPEAKER)
        speaker = speaker[2:-1]  # remove <#...>
        self.emitter.set_speaker(speaker)
        return speaker

    def parse_message(self) -> str:
        """
        message ::= {unknown|soundtag|whitespace}
        """
        message: str = ""

        self.ignore_whitespaces()

        while self.current_token.type in (
                TranscriptTokenType.WHITESPACE,
                TranscriptTokenType.SOUNDTAG,
                TranscriptTokenType.UNKNOWN):
            message = f"{message}{self.consume_token()}"
        else:
            message = message.rstrip()
            assert len(message) > 0, "Expecting message tokens, found none"

        return message

    def ignore_whitespaces(self):
        while self.check_current_token(TranscriptTokenType.WHITESPACE):
            self.consume_token()
