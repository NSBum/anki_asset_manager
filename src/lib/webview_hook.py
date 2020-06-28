from aqt import mw
from aqt.reviewer import Reviewer
from aqt.webview import WebContent

from ..config import maybe_get_setting_from_card
from .stringify import stringify_setting

addon_package = mw.addonManager.addonFromModule(__name__)

def append_scripts(web_content: WebContent, context):
    if not isinstance(context, Reviewer):
        return

    setting = maybe_get_setting_from_card(context.card)

    if not setting:
        return

    # web_content.css.append(
    #     f"/_addons/{addon_package}/web/my-addon.css")
    # web_content.js.append(
    #     f"/_addons/{addon_package}/web/my-addon.js")

    model_name = context.card.model()['name']
    template_name = context.card.template()['name']

    web_content.head += stringify_setting(setting, model_name, template_name, 'question', 'head')
    web_content.body += stringify_setting(setting, model_name, template_name, 'question', 'body')
