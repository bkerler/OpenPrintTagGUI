def is_supported_reader(name):
    """Match supported contactless interfaces, excluding secure access modules."""
    name = str(name).upper()
    return ("ACR1552" in name or name.startswith("VMWARE ")) and "SAM" not in name
