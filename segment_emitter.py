from dataclasses import dataclass, field, asdict
import json


@dataclass
class Segment:
    speaker_tag: str = ""
    text: str = ""
    start: int = 0
    end: int = 0


@dataclass
class SegmentEmitter:
    is_merge_next: bool = False
    segment: Segment = field(init=False)
    utterance_start: int = field(default="", init=False)
    utterance_end: int = field(default="", init=False)

    def __post_init__(self):
        self.segment = Segment()

    def compute_segment_end(self, offset: int) -> int:
        return self.utterance_start + offset

    def use_default_segment_end(self):
        self.segment.end = self.utterance_end

    def use_default_segment_start(self):
        self.segment.start = self.utterance_start

    def set_segment_start(self, start):
        self.segment.start = start

    def set_segment_end(self, end):
        self.segment.end = end

    def set_merge_next(self):
        self.is_merge_next = True

    def unset_merge_next(self):
        self.is_merge_next = False

    def reset(self):
        self.segment = Segment()

    def set_meta_key(self, meta: str, value: str):
        pass

    def set_interval_start(self, start: int):
        self.utterance_start = start

    def set_interval_end(self, end: int):
        self.utterance_end = end

    def set_speaker(self, speaker: str):
        self.segment.speaker_tag = speaker

    def set_message(self, message):
        self.segment.text = message

    def append_message(self, message):
        self.segment.text = f"{self.segment.text} {message}"

    def is_ready(self):
        return not self.is_merge_next

    def emit(self):
        print(json.dumps(asdict(self.segment), indent=4))
        # with open("segments.json", "a") as fh:
        #     fh.write(json.dumps(asdict(self.segment), indent=4))
        #     fh.write("\n")

        self.reset()
