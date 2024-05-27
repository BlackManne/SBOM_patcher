packet_size = 10
PACKET_SIZE_TYPE_SIZE = 4
CRC_SIZE = 50
CRSF_MAX_PACKET_LEN = 100
PARSER_STATE_HEADER = "PARSING"
HEADER_SIZE = 10
PARSING_STATE = "PARSING"


def trial_func(parser_statistics):
    working_segment_size = packet_size + PACKET_SIZE_TYPE_SIZE
    if working_segment_size > CRSF_MAX_PACKET_LEN:
        parser_statistics += 1
        parser_state = PARSER_STATE_HEADER
        working_segment_size = HEADER_SIZE
        if parser_state == PARSING_STATE:
            print_parsing_state(parser_statistics, parser_state, working_segment_size)
        else:
            print("not parsing...")


def print_parsing_state(_parser_statistics, _parser_state, _working_segment_size):
    print("parsing state now is: ")
    print("parsing statistics: " + _parser_statistics)
    print("parsing state: " + _parser_state)
    print("working segment size: " + _working_segment_size)