from attrs import define, field


@define
class Note:
    content: str = field(default="")
    title: str = field(default="")
    bg_index: int = field(default=0)
    
    def copy_data(self, note: "Note"):
        self.content = note.content
        self.title = note.title
        self.bg_index = note.bg_index
