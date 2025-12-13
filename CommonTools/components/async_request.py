from attrs import define, field

from .async_core import ResourceContext


@define
class ImageContext(ResourceContext):
    namespace: str = field(default="images", init=False)
