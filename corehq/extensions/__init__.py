from corehq.extensions.interface import CommCareExtensions, ExtensionError   # noqa

extension_manager = CommCareExtensions()

register_extension_point = extension_manager.register_extension_point
register_extension = extension_manager.register_extension
get_contributions = extension_manager.get_extension_point_contributions
