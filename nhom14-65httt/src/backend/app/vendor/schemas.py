"""Schema vendor tái sử dụng validation quán và không cho sửa trạng thái duyệt."""

from app.menu.schemas import MenuItemCreate, MenuItemUpdate
from app.restaurants.schemas import RestaurantCreate, RestaurantUpdate


class VendorRestaurantCreate(RestaurantCreate):
    pass


class VendorRestaurantUpdate(RestaurantUpdate):
    pass


class VendorMenuItemCreate(MenuItemCreate):
    pass


class VendorMenuItemUpdate(MenuItemUpdate):
    pass
