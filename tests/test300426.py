from typing import Annotated

from network.messages import BaseMessage
from network.messages.core import BaseActionType

from pydantic import SecretStr, Field

class TestActionType(BaseActionType):
    TEST = "test", "test", "test"
    
class TestMessage(BaseMessage, type=TestActionType.TEST):
    msg: Annotated[SecretStr, Field(json_schema_extra=dict(is_socket=True))]
    
    
a = TestMessage(msg="test")
print(a.to_str())