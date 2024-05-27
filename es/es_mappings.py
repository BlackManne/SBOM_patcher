nvd_mappings = \
    {
        "properties": {
            "No": {"type": "text"},
            "title": {"type": "text"},
            "description": {"type": "text"},
            "score": {"type": "text"},
            "source_url": {"type": "text"},
            "affected_software": {
                "type": "nested",
                "properties": {
                    "software_name": {
                        "type": "text",
                    },
                    "versions": {
                        "type": "nested"
                    },
                    "versions_raw": {
                        "type": "text"
                    }
                }
            },
            "third_party_list": {"type": "nested"},
            "vendor_list": {"type": "nested"},
            "exploit_list": {"type": "nested"},
            "patch_list": {
                "type": "nested",
                "properties": {
                    "time": {
                        "type": "date"
                    },
                    "patch_url": {
                        "type": "text"
                    },
                    "service_name": {
                        "type": "text"
                    },
                    "patch_detail": {
                        "type": "nested"
                    }
                }
            }
        }
    }

# relation_mappings = \
#     {
#         "properties": {
#             "software": {"type": "text"},
#             "related_cve": {
#                 "type": "nested",
#                 "properties": {
#                     "cve_number": {"type": "text"}
#                 }
#             }
#         }
#     }
