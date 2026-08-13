from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[Any] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "Success") -> "StandardResponse":
        return cls(success=True, message=message, data=data, errors=None)

    @classmethod
    def fail(cls, message: str = "Error occurred", errors: Any = None) -> "StandardResponse":
        return cls(success=False, message=message, data=None, errors=errors)
