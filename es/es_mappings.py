nvd_mappings = \
    {
        "dynamic": True,  # 启用动态映射
        "properties": {
            "No": {"type": "keyword"},
            "title": {"type": "text"},
            "description": {"type": "nested"},
            "score": {"type": "text"},
            "source_urls": {"type": "nested"},
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
                        "type": "text",
                    },
                    "detail_versions": {
                        "type": "text",
                    },
                    "raw_versions": {
                        "type": "text",
                    }
                }
            },
            "third_party_list": {"type": "text"},
            "vendor_list": {"type": "text"},
            "exploit_list": {"type": "text"},
            "patch_list": {
                "type": "nested",
                "properties": {
                    "nvd": {
                        "type": "nested",
                        "properties": {
                            "time": {"type": "text"},
                            "patch_url": {"type": "text"},
                            "service_name": {"type": "text"},
                            "patch_detail": {
                                "type": "object",
                                "dynamic": True,
                            }
                        }
                    },
                    "alicloud": {
                        "type": "nested",
                        "properties": {
                            "time": {"type": "text"},
                            "patch_url": {"type": "text"},
                            "service_name": {"type": "text"},
                            "patch_detail": {
                                "type": "object",
                                "dynamic": True,
                            }
                        }
                    },
                    "debian": {
                        "type": "nested",
                        "properties": {
                            "time": {"type": "text"},
                            "patch_url": {"type": "text"},
                            "service_name": {"type": "text"},
                            "patch_detail": {
                                "type": "object",
                                "dynamic": True,
                            }
                        }
                    },
                }
            },
        }
    }
