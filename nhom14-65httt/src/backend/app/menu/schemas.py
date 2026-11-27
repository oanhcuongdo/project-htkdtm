"""Schema tách món chuẩn, món bán và nguyên liệu thực tế."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

EntityId = Annotated[int, Field(strict=True, gt=0, le=2**31 - 1)]
Price = Annotated[int, Field(strict=True, gt=0, le=10_000_000)]
SpiceLevel = Annotated[int, Field(strict=True, ge=0, le=3)]
Choice = Annotated[str, Field(min_length=1, max_length=100)]
SourceId = Annotated[str, Field(min_length=1, max_length=120)]


class IngredientInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class CanonicalDishCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=180)
    region: str = Field(min_length=1, max_length=40)
    method: str = Field(min_length=1, max_length=40)
    spice_level: SpiceLevel = 0
    ingredients: list[Choice] = Field(default_factory=list, max_length=100)
    labels: list[Choice] = Field(default_factory=list, max_length=100)
    source_id: SourceId | None = None

    @field_validator("name", "region", "method", "source_id", mode="before")
    @classmethod
    def clean_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("ingredients", "labels", mode="before")
    @classmethod
    def clean_choices(cls, value, info):
        if not isinstance(value, list):
            raise ValueError("Đặc trưng phải là danh sách chuỗi.")
        if len(value) > 100:
            raise ValueError("Danh sách đặc trưng không được quá 100 mục.")
        choices, seen = [], set()
        for entry in value:
            if not isinstance(entry, str) or not entry.strip():
                raise ValueError("Đặc trưng không nhận chuỗi rỗng hoặc giá trị khác chuỗi.")
            cleaned = entry.strip().lower() if info.field_name == "ingredients" else entry.strip()
            if cleaned.casefold() not in seen:
                choices.append(cleaned)
                seen.add(cleaned.casefold())
        return choices


class CanonicalDishUpdate(CanonicalDishCreate):
    spice_level: SpiceLevel
    ingredients: list[Choice] = Field(max_length=100)
    labels: list[Choice] = Field(max_length=100)
    source_id: SourceId | None


class MenuItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canonical_dish_id: EntityId
    name: str = Field(min_length=1, max_length=180)
    price: Price
    is_available: StrictBool = False
    ingredients_verified: StrictBool = False
    ingredient_ids: list[EntityId] = Field(default_factory=list, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("ingredient_ids")
    @classmethod
    def unique_ingredients(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Danh sách nguyên liệu không được lặp ID.")
        return value

    @model_validator(mode="after")
    def verified_has_ingredients(self):
        if self.ingredients_verified and not self.ingredient_ids:
            raise ValueError("Cần khai báo nguyên liệu thực tế trước khi xác nhận.")
        return self


class MenuItemUpdate(MenuItemCreate):
    is_available: StrictBool
    ingredients_verified: StrictBool
    ingredient_ids: list[EntityId] = Field(max_length=100)


class IngredientPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class IngredientDetail(IngredientPublic):
    is_simulated: bool


class CanonicalDishPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    region: str
    method: str
    spice_level: int
    ingredients: list[str]
    labels: list[str]


class CanonicalDishDetail(CanonicalDishPublic):
    source_id: str | None
    is_simulated: bool


class MenuItemPublic(BaseModel):
    id: int
    restaurant_id: int
    restaurant_name: str
    canonical_dish_id: int
    name: str
    price: int
    is_available: bool
    ingredients_verified: bool
    canonical_dish: CanonicalDishPublic
    ingredients: list[IngredientPublic]


class MenuItemDetail(MenuItemPublic):
    is_simulated: bool


class MenuItemPage(BaseModel):
    items: list[MenuItemDetail]
    total: int
    offset: int
    limit: int


class CanonicalDishPage(BaseModel):
    items: list[CanonicalDishPublic]
    total: int
    offset: int
    limit: int


class IngredientPage(BaseModel):
    items: list[IngredientPublic]
    total: int
    offset: int
    limit: int
