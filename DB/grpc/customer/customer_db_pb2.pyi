from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
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

class ProductSearchRequest(_message.Message):
    __slots__ = ("session_id", "category", "keywords")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    KEYWORDS_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    category: int
    keywords: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, session_id: _Optional[int] = ..., category: _Optional[int] = ..., keywords: _Optional[_Iterable[str]] = ...) -> None: ...

class ProductSearchResponse(_message.Message):
    __slots__ = ("seller_id", "category", "name", "keywords", "condition_val", "sale_price", "quantity", "thumbs_up", "thumbs_down")
    SELLER_ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    KEYWORDS_FIELD_NUMBER: _ClassVar[int]
    CONDITION_VAL_FIELD_NUMBER: _ClassVar[int]
    SALE_PRICE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    THUMBS_UP_FIELD_NUMBER: _ClassVar[int]
    THUMBS_DOWN_FIELD_NUMBER: _ClassVar[int]
    seller_id: int
    category: int
    name: str
    keywords: _containers.RepeatedScalarFieldContainer[str]
    condition_val: int
    sale_price: float
    quantity: int
    thumbs_up: int
    thumbs_down: int
    def __init__(self, seller_id: _Optional[int] = ..., category: _Optional[int] = ..., name: _Optional[str] = ..., keywords: _Optional[_Iterable[str]] = ..., condition_val: _Optional[int] = ..., sale_price: _Optional[float] = ..., quantity: _Optional[int] = ..., thumbs_up: _Optional[int] = ..., thumbs_down: _Optional[int] = ...) -> None: ...

class ListProductResponse(_message.Message):
    __slots__ = ("items", "status", "message")
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[ProductSearchResponse]
    status: Status
    message: str
    def __init__(self, items: _Optional[_Iterable[_Union[ProductSearchResponse, _Mapping]]] = ..., status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...

class AddItemToCartRequest(_message.Message):
    __slots__ = ("item_id", "quantity", "session_id")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    item_id: int
    quantity: int
    session_id: int
    def __init__(self, item_id: _Optional[int] = ..., quantity: _Optional[int] = ..., session_id: _Optional[int] = ...) -> None: ...

class AddItemToCartResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...

class GetItemRequest(_message.Message):
    __slots__ = ("session_id", "item_id")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ...) -> None: ...

class ItemType(_message.Message):
    __slots__ = ("item_id", "seller_id", "category", "name", "keywords", "condition", "sale_price", "quantity", "thumbs_up", "thumbs_down")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SELLER_ID_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    KEYWORDS_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    SALE_PRICE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    THUMBS_UP_FIELD_NUMBER: _ClassVar[int]
    THUMBS_DOWN_FIELD_NUMBER: _ClassVar[int]
    item_id: int
    seller_id: int
    category: int
    name: str
    keywords: str
    condition: int
    sale_price: float
    quantity: int
    thumbs_up: int
    thumbs_down: int
    def __init__(self, item_id: _Optional[int] = ..., seller_id: _Optional[int] = ..., category: _Optional[int] = ..., name: _Optional[str] = ..., keywords: _Optional[str] = ..., condition: _Optional[int] = ..., sale_price: _Optional[float] = ..., quantity: _Optional[int] = ..., thumbs_up: _Optional[int] = ..., thumbs_down: _Optional[int] = ...) -> None: ...

class GetItemResponse(_message.Message):
    __slots__ = ("status", "message", "item")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ITEM_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    item: ItemType
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ..., item: _Optional[_Union[ItemType, _Mapping]] = ...) -> None: ...

class RemoveItemFromCartRequest(_message.Message):
    __slots__ = ("session_id", "item_id")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ...) -> None: ...

class RemoveItemFromCartResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...

class SaveCartResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...

class ItemInCart(_message.Message):
    __slots__ = ("item_id", "quantity")
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    item_id: int
    quantity: int
    def __init__(self, item_id: _Optional[int] = ..., quantity: _Optional[int] = ...) -> None: ...

class DisplayCartResponse(_message.Message):
    __slots__ = ("status", "message", "items")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    items: _containers.RepeatedCompositeFieldContainer[ItemInCart]
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ..., items: _Optional[_Iterable[_Union[ItemInCart, _Mapping]]] = ...) -> None: ...

class ClearCartResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...

class ProvideFeedbackRequest(_message.Message):
    __slots__ = ("session_id", "item_id", "feedback")
    class FeedbackType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UP: _ClassVar[ProvideFeedbackRequest.FeedbackType]
        DOWN: _ClassVar[ProvideFeedbackRequest.FeedbackType]
    UP: ProvideFeedbackRequest.FeedbackType
    DOWN: ProvideFeedbackRequest.FeedbackType
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    FEEDBACK_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    feedback: ProvideFeedbackRequest.FeedbackType
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ..., feedback: _Optional[_Union[ProvideFeedbackRequest.FeedbackType, str]] = ...) -> None: ...

class ProvideFeedbackResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...

class GetSellerRatingForBuyerRequest(_message.Message):
    __slots__ = ("session_id", "seller_id")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    SELLER_ID_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    seller_id: int
    def __init__(self, session_id: _Optional[int] = ..., seller_id: _Optional[int] = ...) -> None: ...

class GetSellerRatingForBuyerResponse(_message.Message):
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

class GetBuyerPurchasesResponse(_message.Message):
    __slots__ = ("status", "message", "purchases")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    PURCHASES_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    purchases: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ..., purchases: _Optional[_Iterable[str]] = ...) -> None: ...

class MakePurchaseResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...

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

class RegisterItemForSaleRequest(_message.Message):
    __slots__ = ("session_id", "name", "category", "keywords", "condition", "sale_price", "quantity")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CATEGORY_FIELD_NUMBER: _ClassVar[int]
    KEYWORDS_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    SALE_PRICE_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    name: str
    category: int
    keywords: _containers.RepeatedScalarFieldContainer[str]
    condition: int
    sale_price: float
    quantity: int
    def __init__(self, session_id: _Optional[int] = ..., name: _Optional[str] = ..., category: _Optional[int] = ..., keywords: _Optional[_Iterable[str]] = ..., condition: _Optional[int] = ..., sale_price: _Optional[float] = ..., quantity: _Optional[int] = ...) -> None: ...

class RegisterItemForSaleResponse(_message.Message):
    __slots__ = ("status", "message", "item_id")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    item_id: int
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ..., item_id: _Optional[int] = ...) -> None: ...

class ChangeItemPriceRequest(_message.Message):
    __slots__ = ("session_id", "item_id", "sale_price")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    ITEM_ID_FIELD_NUMBER: _ClassVar[int]
    SALE_PRICE_FIELD_NUMBER: _ClassVar[int]
    session_id: int
    item_id: int
    sale_price: float
    def __init__(self, session_id: _Optional[int] = ..., item_id: _Optional[int] = ..., sale_price: _Optional[float] = ...) -> None: ...

class ChangeItemPriceResponse(_message.Message):
    __slots__ = ("status", "message")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    status: Status
    message: str
    def __init__(self, status: _Optional[_Union[Status, str]] = ..., message: _Optional[str] = ...) -> None: ...
