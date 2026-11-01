from core.utils.urls import URL_MAPPING_TYPE, resolve_and_build_paths

core_url_mapping: URL_MAPPING_TYPE = (
    # ("url_file", "version", "url_path")
    ("core.apps.users.urls", "v1", "users"),
    ("core.apps.crm.urls", "v1", "customers"),
)

core_api_url_patterns = resolve_and_build_paths(core_url_mapping)
