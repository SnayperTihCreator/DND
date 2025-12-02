import re

"""
MIME formats:
1) INPUT FORMAT - <token-type>:<args>
2) RUNTIME FORMAT - <token-type>:<args1>:<args2>:<args3>
"""

MIME_INPUT_FORMAT = re.compile(r"^(\w+):(.+)$")
MIME_RUNTIME_FORMAT = re.compile(r"^(\w+):([^:]+):([^:]+)(?::([^:]+))?$")

FORBIDDEN_CHARS = re.compile(r"[|:@\n\r\t\"'`\\<>,%]")
