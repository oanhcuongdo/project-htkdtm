import NotFoundPage from "./pages/NotFoundPage";
import { Link, Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import RoleGuard from "./components/layout/RoleGuard";
import HomePage from "./pages/HomePage";
import AccountPage from "./pages/AccountPage";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import PreferencePage from "./pages/customer/PreferencePage";
import SearchPage from "./pages/customer/SearchPage";
import RestaurantPage from "./pages/customer/RestaurantPage";
import DishDetailPage from "./pages/customer/DishDetailPage";
import CartPage from "./pages/customer/CartPage";
import CheckoutPage from "./pages/customer/CheckoutPage";
import OrderListPage from "./pages/customer/OrderListPage";
import OrderDetailPage from "./pages/customer/OrderDetailPage";
import VendorProfilePage from "./pages/vendor/ProfilePage";
import VendorDashboardPage from "./pages/vendor/DashboardPage";
import VendorOrderManagePage from "./pages/vendor/OrderManagePage";
import VendorOrderDetailPage from "./pages/vendor/OrderDetailPage";
import VendorMenuPage from "./pages/vendor/MenuManagePage";
import VendorMenuItemPage from "./pages/vendor/MenuItemPage";
import { CartProvider } from "./contexts/CartContext";
import AdminRestaurantManagePage from "./pages/admin/RestaurantManagePage";
import AdminDashboardPage from "./pages/admin/DashboardPage";
import IngredientCatalogPage from "./pages/admin/IngredientCatalogPage";
import DishCatalogPage from "./pages/admin/DishCatalogPage";

export default function AppRouter() {
  return (
    <CartProvider>
      <Routes>
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="restaurants/:id" element={<RestaurantPage />} />
          <Route path="menu-items/:id" element={<DishDetailPage />} />
          <Route path="cart" element={<CartPage />} />
          <Route element={<RoleGuard />}>
            <Route path="account" element={<AccountPage />} />
          </Route>
          <Route element={<RoleGuard roles={["vendor"]} />}>
            <Route path="vendor" element={<AccountPage />} />
            <Route path="vendor/dashboard" element={<VendorDashboardPage />} />
            <Route path="vendor/profile" element={<VendorProfilePage />} />
            <Route path="vendor/orders" element={<VendorOrderManagePage />} />
            <Route
              path="vendor/orders/:id"
              element={<VendorOrderDetailPage />}
            />
            <Route path="vendor/menu" element={<VendorMenuPage />} />
            <Route path="vendor/menu/new" element={<VendorMenuItemPage />} />
            <Route
              path="vendor/menu/:id/edit"
              element={<VendorMenuItemPage />}
            />
          </Route>
          <Route element={<RoleGuard roles={["customer"]} />}>
            <Route path="checkout" element={<CheckoutPage />} />
            <Route path="orders" element={<OrderListPage />} />
            <Route path="orders/:id" element={<OrderDetailPage />} />
            <Route path="onboarding/taste" element={<PreferencePage />} />
          </Route>
          <Route element={<RoleGuard roles={["admin"]} />}>
            <Route path="admin" element={<AccountPage />} />
            <Route path="admin/dashboard" element={<AdminDashboardPage />} />
            <Route path="admin/dishes" element={<DishCatalogPage />} />
            <Route
              path="admin/ingredients"
              element={<IngredientCatalogPage />}
            />
            <Route
              path="admin/restaurants"
              element={<AdminRestaurantManagePage />}
            />
          </Route>
          <Route
            path="forbidden"
            element={
              <section className="status-card">
                <span className="eyebrow">QUYỀN TRUY CẬP</span>
                <h1>Trang này dành cho vai trò khác.</h1>
                <p>
                  Bạn có thể quay lại trang chủ hoặc đăng nhập bằng tài khoản
                  phù hợp.
                </p>
                <Link className="button" to="/">
                  Về trang chủ
                </Link>
              </section>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </CartProvider>
  );
}
