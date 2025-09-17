import uuid


def uuid_to_bin(u: str) -> bytes:
    return uuid.UUID(u).bytes


def bin_to_uuid(b: bytes) -> str:
    return str(uuid.UUID(bytes=b))
