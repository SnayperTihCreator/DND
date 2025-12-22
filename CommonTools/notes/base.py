from attrs import define, field


@define
class Note:
    text: str = field(default="")
    title: str = field(default="")
    bg_index: int = field(default=0)
