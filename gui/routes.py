from gui.router import Router, DataStrategy
# from gui.views.home import HomeView
# from gui.views.settings_view import SettingsView
# from gui.views.sign_up import SignUpView
# from gui.views.stocks import Stocks
from gui.views import HomeView, SettingsView, SignUpView, Stocks
router = Router(DataStrategy.QUERY)

router.routes = {
  "/": HomeView(router),
  "/settings": SettingsView(router),
  "/sign_up": SignUpView(router),
  "/stocks": Stocks(router),
}