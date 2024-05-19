from io import BytesIO
from PIL import Image

from hsrcard import hsr
from hsrcard.src.tools import modal
from honkairail.src.tools import modalV2

from hoyoapi import HoyoAPI

class HoYoCard(hsr.HonkaiCard):
    def __init__(self, cookies, uid, save=False):
        super().__init__(save=save)
        self.uid = uid
        self.API = HoyoAPI(cookies)

    # fix pydantic errors
    async def collect_data(self):
        player = self.data.player
        if isinstance(player, modalV2.PlayerV2):
            avatar = modal.Avatar(
                id=player.avatar.id,
                name=player.avatar.name,
                icon=player.avatar.icon
            )
            space_info = modal.SpaceInfo(
                pass_area_progress=player.space_info.pass_area_progress,
                light_cone_count=player.space_info.light_cone_count,
                avatar_count=player.space_info.avatar_count,
                achievement_count=player.space_info.achievement_count
            )
        else:
            avatar = modal.Avatar(
                id=None,
                name=None,
                icon=None
            )
            space_info = modal.SpaceInfo(
                pass_area_progress=None,
                light_cone_count=None,
                avatar_count=None,
                achievement_count=None
            )

        return modal.HSRCard(
            settings=modal.Settings(
                uid=int(self.uid),
                lang=self.lang,
                hide=self.hide,
                save=self.save,
                background=False
            ),
            player=modal.PlayerV2(
                uid=player.uid,
                nickname=player.nickname,
                level=player.level,
                avatar=avatar,
                signature=player.signature,
                friend_count=player.friend_count,
                world_level=player.world_level,
                birthday=player.birthday,
                space_info=space_info,
            ),
            card=self.card,
            cards=None,
            name=self.name,
            id=self.id
        )

    async def creat(self, uid: int, char_names: list[str]=[]) -> modal.HSRCard:
        self.API.get_chars = char_names
        return await super().creat(uid)
    
    async def get_availabled_chars(self) -> list[str]:
        result = []
        if self.API.available_chars is None:
            await self.creat(self.uid, []) # TODO: crutch i think
        for char in self.API.available_chars:
            result.append(char)
        return result
    
    async def generate_image(self, name: str) -> BytesIO:
        output = BytesIO()
        result = await self.creat(self.uid, char_names=[name])
        if isinstance(result.card, list) and len(result.card) > 0:
            result.card[0].card.save(output, format="png")
        elif isinstance(result.card, Image.Image):
            result.card.save(output, format="png")
        output.seek(0)
        return output
    
    async def get_character_stats(self) -> list[modalV2.CharacterData]:
        self.API.get_chars = None
        return await self.API.get_starrail_characters(self.uid)