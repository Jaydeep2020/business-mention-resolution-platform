from pydantic import BaseModel, ConfigDict, Field


class CategorySummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(
        from_attributes=True
    )


class BusinessCreate(BaseModel):

    business_id: str = Field(
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    address: str | None = Field(
        default=None,
        max_length=500,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=50,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
    )

    latitude: float | None = None
    longitude: float | None = None

    is_verified: bool = True

    category_ids: list[int] = []


class BusinessUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    address: str | None = Field(
        default=None,
        max_length=500,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=50,
    )

    postal_code: str | None = Field(
        default=None,
        max_length=20,
    )

    latitude: float | None = None
    longitude: float | None = None

    is_verified: bool | None = None

    category_ids: list[int] | None = None


class BusinessResponse(BaseModel):

    id: int

    business_id: str

    name: str

    address: str | None

    city: str | None

    state: str | None

    postal_code: str | None

    latitude: float | None

    longitude: float | None

    is_verified: bool

    categories: list[CategorySummary] = []

    model_config = ConfigDict(
        from_attributes=True
    )


class BusinessListResponse(BaseModel):

    items: list[BusinessResponse]

    page: int
    page_size: int
    total: int
    total_pages: int