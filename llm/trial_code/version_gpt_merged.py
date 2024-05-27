packet_size = 10
PACKET_SIZE_TYPE_SIZE = 4
CRSF_MAX_PACKET_LEN = 100
PARSER_STATE_HEADER = "PARSING"
HEADER_SIZE = 10


def trial_func(parser_statistics):
    working_segment_size = packet_size - PACKET_SIZE_TYPE_SIZE
    if working_segment_size > CRSF_MAX_PACKET_LEN:
        parser_statistics += 1
        parser_state = PARSER_STATE_HEADER
        working_segment_size = HEADER_SIZE
        print("parsing state now is: ")
        print("parsing statistics: " + str(parser_statistics))
        print("parsing state: " + parser_state)
        print("working segment size: " + str(working_segment_size))
    else:
        working_segment_size = packet_size + PACKET_SIZE_TYPE_SIZE
        if working_segment_size > CRSF_MAX_PACKET_LEN:
            parser_statistics += 1
            parser_state = PARSER_STATE_HEADER
            working_segment_size = HEADER_SIZE
            print("parsing state now is: ")
            print("parsing statistics: " + str(parser_statistics))
            print("parsing state: " + parser_state)
            print("working segment size: " + str(working_segment_size))
        else:
            parser_statistics += 1
            parser_state = PARSER_STATE_HEADER
            working_segment_size = HEADER_SIZE
            print("parsing state now is: ")
            print("parsing statistics: " + str(parser_statistics))
            print("parsing state: " + parser_state)
            print("working segment size: " + str(working_segment_size))