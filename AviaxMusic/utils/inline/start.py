import config
from AviaxMusic import app
from pyrogram import enums


def start_panel(self, _):
    buttons = [
        [
            self.ikb(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style=enums.ButtonStyle.PRIMARY,
                icon_custom_emoji_id=5882207227997066107,
            ),
            self.ikb(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
                icon_custom_emoji_id=5192766690609643141,
            ),
        ],
    ]
    return buttons


def private_panel(self, _):
    buttons = [
        [
            self.ikb(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
                icon_custom_emoji_id=5882207227997066107,
            )
        ],
        [
            self.ikb(
                text=_["S_B_4"],
                callback_data="settings_back_helper",
                icon_custom_emoji_id=5465665476971471368,
            )
        ],
        [
            self.ikb(
                text=_["S_B_5"],
                user_id=config.OWNER_ID,
                icon_custom_emoji_id=5433653135799228968,
            ),
            self.ikb(
                text=_["S_B_2"],
                url=config.SUPPORT_GROUP,
                icon_custom_emoji_id=5192766690609643141,
            ),
        ],
        [
            self.ikb(
                text=_["S_B_6"],
                url=config.SUPPORT_CHANNEL,
                icon_custom_emoji_id=5312012419237230426,
            ),
        ],
    ]
    return buttons
