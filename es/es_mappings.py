nvd_mappings = \
    {
        "properties": {
            "No": {"type": "text"},
            "title": {"type": "text"},
            "description": {"type": "text"},
            "score": {"type": "text"},
            "source_url": {"type": "text"},
            "cve_published_time": {
                "type": "text"
            },
            "cve_modified_time": {
                "type": "text"
            },
            "crawl_time": {
                "type": "text"
            },
            "affected_software": {
                "type": "nested",
                "properties": {
                    "software_name": {
                        "type": "text",
                    },
                    "interval_versions": {
                        "type": "nested"
                    },
                    "detail_versions": {
                        "type": "nested"
                    },
                    "raw_versions": {
                        "type": "text"
                    }
                }
            },
            "third_party_list": {"type": "nested"},
            "vendor_list": {"type": "nested"},
            "exploit_list": {"type": "nested"},
            "patch_list": {
                "type": "nested",
                "nvd": {
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
                },
                "alicloud": {
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
                },
                "debian": {
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
                },
            },
            "debian_list": {"type": "nested"},
            "advisories_list": {"type": "nested"}
        }
    }
