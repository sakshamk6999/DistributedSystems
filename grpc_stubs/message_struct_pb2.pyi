import customer_db_pb2 as _customer_db_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GeneralMessage(_message.Message):
    __slots__ = ("request_message", "service_message")
    REQUEST_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SERVICE_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    request_message: RequestMessage
    service_message: ServiceMessage
    def __init__(self, request_message: _Optional[_Union[RequestMessage, _Mapping]] = ..., service_message: _Optional[_Union[ServiceMessage, _Mapping]] = ...) -> None: ...

class RequestMessage(_message.Message):
    __slots__ = ("sender_id", "local_sequence_num", "login_request", "register_request", "metadata")
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    LOCAL_SEQUENCE_NUM_FIELD_NUMBER: _ClassVar[int]
    LOGIN_REQUEST_FIELD_NUMBER: _ClassVar[int]
    REGISTER_REQUEST_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    sender_id: int
    local_sequence_num: int
    login_request: _customer_db_pb2.LoginRequest
    register_request: _customer_db_pb2.RegisterRequest
    metadata: RequestMetadata
    def __init__(self, sender_id: _Optional[int] = ..., local_sequence_num: _Optional[int] = ..., login_request: _Optional[_Union[_customer_db_pb2.LoginRequest, _Mapping]] = ..., register_request: _Optional[_Union[_customer_db_pb2.RegisterRequest, _Mapping]] = ..., metadata: _Optional[_Union[RequestMetadata, _Mapping]] = ...) -> None: ...

class RequestMetadata(_message.Message):
    __slots__ = ("global_sequence",)
    GLOBAL_SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    global_sequence: int
    def __init__(self, global_sequence: _Optional[int] = ...) -> None: ...

class ServiceMessage(_message.Message):
    __slots__ = ("source_id", "request_id", "global_id", "sender_id", "metadata")
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    source_id: int
    request_id: int
    global_id: int
    sender_id: int
    metadata: ServiceMetadata
    def __init__(self, source_id: _Optional[int] = ..., request_id: _Optional[int] = ..., global_id: _Optional[int] = ..., sender_id: _Optional[int] = ..., metadata: _Optional[_Union[ServiceMetadata, _Mapping]] = ...) -> None: ...

class ServiceMetadata(_message.Message):
    __slots__ = ("last_delivered_seq",)
    LAST_DELIVERED_SEQ_FIELD_NUMBER: _ClassVar[int]
    last_delivered_seq: int
    def __init__(self, last_delivered_seq: _Optional[int] = ...) -> None: ...
