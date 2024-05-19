import math

from honkairail import starrailapi
import honkairail.src.tools.modalV2 as modalV2
import genshin

from dm import DM

def convert_element(element):
    return modalV2.ElementV2(
        id="", # TODO
        name=element.capitalize(),
        icon=f"icon/element/{element.capitalize()}.png",
        color="#FFFFFF" # TODO
    )

def convert_path(path):
    paths = [
        "", # none?
        "Destruction",
        "Hunt",
        "Erudition",
        "Harmony",
        "Nihility",
        "Preservation",
        "Abundance",
    ]

    ids = [
        "", # none?
        "Warrior",
        "Rogue",
        "Mage",
        "Shaman",
        "Warlock",
        "Knight",
        "Priest",
    ]

    return modalV2.PathV2(
        id=ids[path],
        name=paths[path],
        icon=f"icon/path/{paths[path]}.png"
    )

def stat_to_icon(stat):
    convert = {
        "ATK Boost": "IconAttack",
        "Break Enhance": "IconBreakUp",
        "CRIT Rate Boost": "IconCriticalChance",
        "CRIT DMG Boost": "IconCriticalDamage",
        "DEF Boost": "IconDefence",
        "?": "IconEnergyRecovery", # TODO
        "DMG Boost: Fire": "IconFireAddedRatio",
        "??": "IconHealRatio", # TODO
        "DMG Boost: Ice": "IconIceAddedRatio",
        "DMG Boost: Imaginary": "IconImaginaryAddedRatio",
        "HP Boost": "IconMaxHP",
        "DMG Boost: Physical": "IconPhysicalAddedRatio",
        "DMG Boost: Quantum": "IconQuantumAddedRatio",
        "SPD Boost": "IconSpeed",
        "Effect Hit Rate Boost": "IconStatusProbability",
        "Effect RES Boost": "IconStatusResistance",
        "DMG Boost: Lightning": "IconThunderAddedRatio",
        "DMG Boost: Wind": "IconWindAddedRatio",
    }

    return f"icon/property/{convert[stat]}.png"

def convert_char_skill(stat, id):
    if stat == "Bonus Ability":
        return f"skilltree{id[-1]}"

    to_path = {
        "Basic ATK": "basic_atk",
        "Skill": "skill",
        "Ultimate": "ultimate",
        "Talent": "talent",
        "Technique": "technique",
    }
    return to_path.get(stat, "")

def convert_property(property, property_info):
    stats = {
        2: "IconAttack",
        58: "IconBreakUp",
        5: "IconCriticalChance",
        6: "IconCriticalDamage",
        3: "IconDefence",
        54: "IconEnergyRecovery",
        14: "IconFireAddedRatio",
        55: "IconHealRatio",
        16: "IconIceAddedRatio",
        24: "IconImaginaryAddedRatio",
        1: "IconMaxHP",
        12: "IconPhysicalAddedRatio",
        22: "IconQuantumAddedRatio",
        4: "IconSpeed",
        10: "IconStatusProbability",
        11: "IconStatusResistance",
        18: "IconThunderAddedRatio",
        20: "IconWindAddedRatio",
    }

    for key, value in stats.items():
        if property_info[str(key)].name == property_info[str(property)].name:
            return f"icon/property/{value}.png"
    return ""

def convert_percent(value: str) -> tuple[bool, float]:
    percent = value.endswith("%")
    result = 0
    if percent:
        result = float(value.replace("%", "")) / 100
    else:
        result = float(value)
    return (percent, result)

class HoyoAPI(starrailapi.StarRailApi):
    def __init__(self, cookies) -> None:
        self.cookies = cookies
        self.client = genshin.Client(cookies)
        self.dm = DM()
        self.get_chars: list[str] = None
        self.available_chars: dict[str, int] = None

    async def create_light_cone(self, data):
        attributes=[
            modalV2.AttributeV2(field="hp", name="hp", icon="icon/property/IconMaxHP.png", value=0, display="-", percent=False),
            modalV2.AttributeV2(field="atk", name="atk", icon="icon/property/IconAttack.png", value=0, display="-", percent=False),
            modalV2.AttributeV2(field="def", name="def", icon="icon/property/IconDefence.png", value=0, display="-", percent=False),
        ]

        id = getattr(data, 'id', 0)
        light_cone = modalV2.LightConeV2(
            id=str(id),
            name=getattr(data, 'name', ''),
            rarity=getattr(data, 'rarity', 3),
            rank=getattr(data, 'rank', 0),
            level=getattr(data, 'level', 0),
            promotion=0, # see create_character
            # icon
            preview=f"image/light_cone_preview/{getattr(data, 'id', 'Icon_TestLightconeMax')}.png",
            portrait=f"image/light_cone_portrait/{getattr(data, 'id', 'Icon_TestLightconeMax')}.png",
            path=None, # TODO
            attributes=attributes,
            properties=[],
        )

        return light_cone

    async def get_char_rank_icon(self, id):
        eidolons = await self.dm.get_eidolons_upgrade(id)
        skill = f"icon/skill/{id}_skill.png"
        ultimate = f"icon/skill/{id}_ultimate.png"

        result = [
            f"icon/skill/{id}_rank1.png",
            f"icon/skill/{id}_rank2.png",
            "",
            f"icon/skill/{id}_rank4.png",
            "",
            f"icon/skill/{id}_rank6.png"
        ]

        result[eidolons[0] - 1] = skill
        result[eidolons[1] - 1] = ultimate

        return result

    async def create_skill(self, data, id):
        model = modalV2.SkillV2(
            id=data.point_id,
            name=data.remake,
            level=data.level,
            max_level=data.level,
            element=None,
            type="",
            type_text="",
            effect="",
            effect_text="",
            simple_desc="",
            desc="",
            icon=f"icon/skill/{id}_{convert_char_skill(data.remake, data.point_id)}.png",
        )

        return model
    
    def create_skill_tree(self, data, id, max_talents):
        level = data.level
        max_level = 1
        icon = f"icon/skill/{id}_{convert_char_skill(data.remake, data.point_id)}.png"

        if data.remake == "Stat Bonus":
            icon = stat_to_icon(data.skill_stages[0].name)
        if not data.is_activated:
            level = 0

        abils = ["Basic ATK", "Skill", "Ultimate", "Talent"]
        try:
            abil_index = abils.index(data.remake)
            max_level = max_talents[abil_index + 1]
        except:
            abil_index = 0

        model = modalV2.SkillTrees(
            id=data.point_id,
            level=level,
            anchor=data.anchor,
            max_level=max_level,
            icon=icon,
            parent=None
        )

        return model

    def create_affix(self, data, property_info):
        percent, value = convert_percent(data.value)
        return modalV2.AffixV2(
            type="",
            field="",
            name="",
            icon=convert_property(data.property_type, property_info),
            value=value,
            display=data.value,
            percent=percent,
        )

    def create_relic(self, data, property_info):
        id = str(data.id)
        set_id = id[1:4]
        pos = data.pos - 1
        if pos >= 4: # planar
            pos -= 4

        sub_affix = []
        for affix in data.properties:
            sub_affix.append(self.create_affix(affix, property_info))

        return modalV2.RelicV2(
            id=id,
            name=data.name,
            set_id=set_id,
            set_name="",
            rarity=data.rarity,
            level=data.level,
            icon=f"icon/relic/{set_id}_{pos}.png",
            main_affix=self.create_affix(data.main_property, property_info),
            sub_affix=sub_affix
        )
    
    def create_attribute(self, data, property_info):
        percent, value = convert_percent(data.base)
        return modalV2.AttributeV2(
            field=property_info[str(data.property_type)].name,
            name=property_info[str(data.property_type)].name,
            icon=convert_property(data.property_type, property_info),
            value=value,
            display=data.base,
            percent=percent
        )

    def create_addition(self, data, property_info):
        percent, value = convert_percent(data.add)
        return modalV2.Addition(
            field=property_info[str(data.property_type)].name,
            name=property_info[str(data.property_type)].name,
            icon=convert_property(data.property_type, property_info),
            value=value,
            display=data.add,
            percent=percent
        )

    def create_property(self, data, property_info):
        percent, value = convert_percent(data.final)
        return modalV2.PropertyV2(
            type="",
            field="",
            name="",
            icon=convert_property(data.property_type, property_info),
            value=value,
            display=data.final,
            percent=percent
        )

    async def create_character(self, data, all_data):
        light_cone = await self.create_light_cone(data.equip)
        max_talents = await self.dm.get_max_talents(data.id, data.rank)

        skills = []
        skill_trees = []
        for skill in data.skills:
            skill_trees.append(self.create_skill_tree(skill, data.id, max_talents))
            if not skill.remake in ["Stat Bonus", "Bonus Ability", "Technique"]:
                skills.append(await self.create_skill(skill, data.id))

        relics = []
        for relic in data.relics:
            relics.append(self.create_relic(relic, all_data.property_info))
        for ornament in data.ornaments:
            relics.append(self.create_relic(ornament, all_data.property_info))

        attributes = []
        additions = []
        properties = []
        for property in data.properties:
            attributes.append(self.create_attribute(property, all_data.property_info))
            additions.append(self.create_addition(property, all_data.property_info))
            # properties.append(self.create_property(property, all_data.property_info))

        char_data = modalV2.CharacterData(
            id=str(data.id),
            name=data.name,
            rarity=data.rarity,
            rank=data.rank,
            level=data.level,
            promotion=6, # see below
            icon=f"icon/character/{data.id}.png",
            preview=f"image/character_preview/{data.id}.png",
            portrait=f"image/character_portrait/{data.id}.png",
            path=convert_path(data.base_type),
            rank_icons=await self.get_char_rank_icon(data.id),
            element=convert_element(data.element),
            skills=skills,
            skill_trees=skill_trees,
            light_cone=light_cone,
            relics=relics,
            relic_sets=[],
            additions=additions,
            attributes=attributes,
            properties=properties,
        )
        
        promotions = await self.dm.get_promotion(data.id, int(light_cone.id), data.level, light_cone.level, int(data.properties[1].base))
        if promotions is not None:
            char_data.promotion = promotions["char"]
            light_cone.promotion = promotions["cone"]

        if light_cone.id != "0":
            base_hp, base_atk, base_def = await self.dm.get_light_cone_stats(int(light_cone.id), light_cone.level, light_cone.promotion)
            attributes = light_cone.attributes

            attributes[0].value = math.floor(base_hp)
            attributes[1].value = math.floor(base_atk)
            attributes[2].value = math.floor(base_def)

            attributes[0].display = str(attributes[0].value)
            attributes[1].display = str(attributes[1].value)
            attributes[2].display = str(attributes[2].value)

        return char_data

    async def get_starrail_user(self,uid):
        self.client.set_cookies(self.cookies)
        data = await self.client.get_starrail_user(uid)
        avatar = modalV2.Avatar(id="", name="", icon="")
        avatar.icon = data.info.avatar
        playerV2 = modalV2.PlayerV2(
            uid=str(uid),
            nickname=data.info.nickname,
            level=data.info.level,
            avatar=avatar,
            signature="",
            friend_count=0,
            world_level=0,
            birthday="",
            space_info=modalV2.SpaceInfo(
                pass_area_progress=0,
                light_cone_count=0,
                avatar_count=len(data.characters),
                achievement_count=data.stats.achievement_num,
            ),
        )
        return playerV2

    async def get_starrail_characters(self, uid):
        self.client.set_cookies(self.cookies)
        data = await self.client.get_starrail_characters(uid)

        self.available_chars = {}
        result = []
        for char in data.avatar_list:
            if self.get_chars is not None and not char.name in self.get_chars:
                self.available_chars[char.name] = char.id
                continue
            result.append(await self.create_character(char, data))
        return result
    
    async def get_full_data(self, uid):
        player = await self.get_starrail_user(uid)
        characters = await self.get_starrail_characters(uid)
        return modalV2.StarRailApiDataV2(player=player, characters=characters)