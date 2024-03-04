from gui.router import Router, DataStrategy
from gui.views import HomeView, SettingsView, SignUpView, Stocks

router = Router(DataStrategy.QUERY)

router.routes = {
  "/": HomeView(router),
  "/settings": SettingsView(router),
  "/sign_up": SignUpView(router),
  "/stocks": Stocks(router),
}