import os
import json
import httpx

def get_assumed_promotion(upgrade_stat, lvl):
    result = []
    for idx, stat in enumerate(upgrade_stat):
        if lvl > stat["maxLevel"]:
            continue

        result.append(idx)
        if lvl == stat["maxLevel"] and idx != len(upgrade_stat) - 1:
            result.append(idx + 1)
        break
    return result

def calc_stat(base, add, lvl):
    return base + add * (lvl - 1)

class DM():
    def __init__(self):
        self.cache = {}
        self.file_path = os.path.join(os.getcwd(), "dm")
        self.url = "https://api.yatta.top/hsr/v2/en"
    
        os.makedirs(os.path.join(self.file_path, "avatar"), exist_ok=True)
        os.makedirs(os.path.join(self.file_path, "equipment"), exist_ok=True)

    async def download_from(self, path):
        if path in self.cache:
            return self.cache[path]

        # open the file
        file_path = os.path.join(self.file_path, path)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                result = json.load(file)
                self.cache[path] = result
                return result

        # if the file doesn't exist, download it
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/{path}")
            result = response.json()

            with open(file_path, 'w') as file:
                json.dump(result, file)

            self.cache[path] = result
            return result
    
    async def get_char_info(self, id):
        return await self.download_from(f"avatar/{id}")
    
    async def get_cone_info(self, id):
        return await self.download_from(f"equipment/{id}")

    async def get_char_promotion(self, char_id, char_lvl, base_atk):
        char = await self.get_char_info(char_id)
        char_assumed = get_assumed_promotion(char["data"]["upgrade"], char_lvl)

        for idx in char_assumed:
            char_upgrade = char["data"]["upgrade"][idx]
            char_atk = calc_stat(char_upgrade["skillBase"]["attackBase"],  char_upgrade["skillAdd"]["attackAdd"], char_lvl)

            if char_atk >= base_atk:
                return { "char": idx, "cone": 0 }

        return None
    
    async def get_promotion(self, char_id, cone_id, char_lvl, cone_lvl, base_atk):
        if cone_id == 0:
            return await self.get_char_promotion(char_id, char_lvl, base_atk)

        char = await self.get_char_info(char_id)
        cone = await self.get_cone_info(cone_id)

        char_assumed = get_assumed_promotion(char["data"]["upgrade"], char_lvl)
        cone_assumed = get_assumed_promotion(cone["data"]["upgrade"], cone_lvl)

        for idx in char_assumed:
            char_upgrade = char["data"]["upgrade"][idx]
            char_atk = calc_stat(char_upgrade["skillBase"]["attackBase"], char_upgrade["skillAdd"]["attackAdd"], char_lvl)

            for jdx in cone_assumed:
                cone_upgrade = cone["data"]["upgrade"][jdx]
                cone_atk = calc_stat(cone_upgrade["skillBase"]["attackBase"],  cone_upgrade["skillAdd"]["attackAdd"], cone_lvl)

                if char_atk + cone_atk >= base_atk:
                    return { "char": idx, "cone": jdx }

        return None
    
    async def get_light_cone_stats(self, cone_id, cone_lvl, cone_promotion):
        cone = await self.get_cone_info(cone_id)
        upgrade = cone["data"]["upgrade"][cone_promotion]

        base_hp = calc_stat(upgrade["skillBase"]["hPBase"], upgrade["skillAdd"]["hPAdd"], cone_lvl)
        base_atk = calc_stat(upgrade["skillBase"]["attackBase"], upgrade["skillAdd"]["attackAdd"], cone_lvl)
        base_def = calc_stat(upgrade["skillBase"]["defenceBase"], upgrade["skillAdd"]["defenceAdd"], cone_lvl)

        return base_hp, base_atk, base_def
    
    # what is first, skill or ultimate?
    async def get_eidolons_upgrade(self, char_id):
        char = await self.get_char_info(char_id)
        eidolons = char["data"]["eidolons"]

        for key, value in eidolons.items():
            if value["rank"] == 3 and value["icon"].endswith("_BP"):
                return [3, 5]
        
        return [5, 3]
    
    async def get_max_talents(self, char_id, eidolons):
        char = await self.get_char_info(char_id)

        result = {}

        for key, value in char["data"]["traces"]["mainSkills"].items():
            id = value["id"] % 10
            result[id] = value["maxLevel"]

        for key, value in char["data"]["eidolons"].items():
            if value["rank"] > eidolons:
                break
            if value["skillAddLevelList"] is None:
                continue
            for tal, upgrade in value["skillAddLevelList"].items():
                id = int(tal) % 10
                result[id] = result.get(id, 0) + upgrade

        return result