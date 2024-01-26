from Router import Router, DataStrategy
from views.home import HomeView
from views.settings_view import SettingsView
from views.sign_up import SignUpView

router = Router(DataStrategy.QUERY)

router.routes = {
  "/": HomeView(router),
  "/settings": SettingsView(router),
  "/sign_up": SignUpView(router),
}