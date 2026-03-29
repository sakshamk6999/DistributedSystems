from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OK: _ClassVar[Status]
    ERROR: _ClassVar[Status]

class CustomerType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BUYER: _ClassVar[CustomerType]
    SELLER: _ClassVar[CustomerType]
OK: Status
ERROR: Status
BUYER: CustomerType
SELLER: CustomerType

class RegisterRequest(_message.Message):
    __slots__ = ("username", "password", "name", "customer_type")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_TYPE_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    name: str
    customer_type: CustomerType
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ..., name: _Optional[str] = ..., customer_type: _Optional[_Union[CustomerType, str]] = ...) -> None: ...

class RegisterResponse(_message.Message):
    __slots__ = ("status", "message", "id")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    id: int
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ..., id: _Optional[int] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ("username", "password", "customer_type")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_TYPE_FIELD_NUMBER: _ClassVar[int]
    username: str
    password: str
    customer_type: CustomerType
    def __init__(self, username: _Optional[str] = ..., password: _Optional[str] = ..., customer_type: _Optional[_Union[CustomerType, str]] = ...) -> None: ...

class LogoutRequest(_message.Message):
    __slots__ = ("session_id", "customer_type")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_TYPE_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    customer_type: CustomerType
    def __init__(self, session_id: _Optional[int] = ..., customer_type: _Optional[_Union[CustomerType, str]] = ...) -> None: ...

class UserRequest(_message.Message):
    __slots__ = ("session_id",)
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    def __init__(self, session_id: _Optional[int] = ...) -> None: ...

class UserResponse(_message.Message):
    __slots__ = ("status", "message", "session_id")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    session_id: int
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ..., session_id: _Optional[int] = ...) -> None: ...

class GetSellerRatingRequest(_message.Message):
    __slots__ = ("session_id", "seller_id", "customer_type")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SELLER_ID_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_TYPE_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    seller_id: int
    customer_type: CustomerType
    def __init__(self, session_id: _Optional[int] = ..., seller_id: _Optional[int] = ..., customer_type: _Optional[_Union[CustomerType, str]] = ...) -> None: ...

class GetSellerRatingResponse(_message.Message):
    __slots__ = ("status", "message", "thumbs_up", "thumbs_down")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    THUMBS_UP_FIELD_NUMBER: _ClassVar[int]
    THUMBS_DOWN_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    thumbs_up: int
    thumbs_down: int
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ..., thumbs_up: _Optional[int] = ..., thumbs_down: _Optional[int] = ...) -> None: ...
