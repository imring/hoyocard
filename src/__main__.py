import os
import interactions

from hoyocard import HoYoCard
from db import User

rarity_emoji = {
    4: ":purple_circle:",
    5: ":yellow_circle:",
}

bot = interactions.Client(
    intents=interactions.Intents.DEFAULT | interactions.Intents.MESSAGE_CONTENT,
    sync_interactions=True,
    asyncio_debug=True,
    token=os.getenv('TOKEN')
)

def get_user_data(user_id: int) -> User | None:
    return User.get_or_none(user_id=user_id)

async def generate_message(
    user_id: int,
    name: str,
    chars_offset: int = 0
) -> tuple[interactions.File | str, interactions.BaseComponent]:
    user = get_user_data(user_id)
    if user is None:
        return "User not found. Please register.", None

    uid = user.uid
    cookies = { "ltuid_v2": user.ltuid, "ltoken_v2": user.ltoken }

    cardgen = HoYoCard(cookies, uid)
    result = await cardgen.generate_image(name)
    chars = (await cardgen.get_availabled_chars())[chars_offset:chars_offset+25]

    components = interactions.StringSelectMenu(
        *chars,
        custom_id="char_select",
        placeholder="Select a character",
    )

    if result is None or result.getbuffer().nbytes == 0:
        return "Character not found", components
    
    # TODO: buttons for chars_offset soon...

    file = interactions.File(file=result, file_name="card.png")
    return file, components


@interactions.slash_command(name="card", description="Generate a card")
@interactions.slash_option(
    name="name",
    description="Name character",
    required=True,
    opt_type=interactions.OptionType.STRING
)
async def card(ctx: interactions.SlashContext, name: str):
    await ctx.defer()

    file, components = await generate_message(int(ctx.author_id), name)
    if isinstance(file, str):
        await ctx.send(file, components=components)
    await ctx.send(file=file, components=components)

@interactions.component_callback("char_select")
async def char_select(ctx: interactions.ComponentContext):
    await ctx.defer(edit_origin=True)
    
    file, components = await generate_message(int(ctx.author_id), ctx.values[0])
    if isinstance(file, str):
        await ctx.edit_origin(file, components=components)
    await ctx.edit_origin(file=file, components=components)

@interactions.slash_command(name="char_list", description="List your characters")
async def char_list(ctx: interactions.SlashContext):
    await ctx.defer()

    user = get_user_data(int(ctx.author_id))
    if user is None:
        await ctx.send("User not found. Please register.")
        return
    uid = user.uid
    cookies = { "ltuid_v2": user.ltuid, "ltoken_v2": user.ltoken }

    cardgen = HoYoCard(cookies, uid)
    chars = await cardgen.get_character_stats()

    fields = []
    for i in range(6, -1, -1):
        chars_ascension = list(filter(lambda x: x.promotion == i, chars))
        str_chars = list(map(lambda x: f"{rarity_emoji[x.rarity]} **{x.name}** E{x.rank} - {x.level}/{20+i*10}", chars_ascension))
        fields.append(
            interactions.EmbedField(
                name=f"Ascension {i}",
                value="\n".join(str_chars) or "-",
                inline=True
            )
        )

    embed = interactions.Embed(
        title="Your characters",
        fields=fields
    )
    await ctx.send(embed=embed)

# TODO: interactions has no text inputs, so...
# DON'T DO THIS
@interactions.slash_command(name="register", description="Register your account")
@interactions.slash_option(name="uid", description="Your UID", required=True, opt_type=interactions.OptionType.INTEGER)
@interactions.slash_option(name="ltoken", description="Your LToken", required=True, opt_type=interactions.OptionType.STRING)
@interactions.slash_option(name="ltuid", description="Your LTUID", required=True, opt_type=interactions.OptionType.STRING)
async def register(ctx: interactions.SlashContext, uid: int, ltoken: str, ltuid: str):
    await ctx.defer()

    if ctx.guild_id is not None:
        await ctx.send("Use DM to register.")
        return

    user = User.create(
        user_id=int(ctx.author_id),
        uid=uid,
        ltuid=ltuid,
        ltoken=ltoken
    )
    await ctx.send(f"Registered as {ctx.author.username} - {uid}", ephemeral=True)

@interactions.listen()
async def on_ready():
    print(f"Logged in as {bot.user.username} - {bot.user.id}")

bot.start()