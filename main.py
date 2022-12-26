from extract_lexer import ExtractLexer
from extract_parser import ExtractParser
from segment_emitter import SegmentEmitter


def main():
    print("Transcription Parser")

    input_transcription = "extract.txt"
    extract_lexer = ExtractLexer(input_transcription)
    emitter: SegmentEmitter = SegmentEmitter()
    extract_parser = ExtractParser(extract_lexer, emitter)

    extract_parser.parse()


if __name__ == '__main__':
    # main()
    main()
