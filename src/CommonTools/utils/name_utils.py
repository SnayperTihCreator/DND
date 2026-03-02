import re

"""
MIME formats:
1) INPUT FORMAT - <token-type>:<args>
2) RUNTIME FORMAT - <token-type>:<args1>:<args2>:<args3>
"""

MIME_INPUT_FORMAT = re.compile(r"^(\w+):(.+)$")
MIME_RUNTIME_FORMAT = re.compile(r"^(\w+):([^:]+):([^:]+)(?::([^:]+))?$")

FORBIDDEN_CHARS = re.compile(r"[|:@\n\r\t\"'`\\<>,%\-]")


def getImageMIME(mime: str) -> str:
    if not mime:
        return ""
    match = MIME_RUNTIME_FORMAT.match(mime)
    
    if match:
        ttype, name, number, _ = match.groups()
        
        if (ttype in ('mob', 'npc')) and (number != "None"):
            return f"token-{ttype}-{name}"
    return f"token-{mime.replace(':', '-')}"
