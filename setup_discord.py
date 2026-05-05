import discord
import asyncio
import os

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
TOKEN    = os.getenv("DISCORD_TOKEN", "TON_TOKEN_ICI")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "TON_GUILD_ID_ICI"))
# ──────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

async def delete_existing(guild: discord.Guild):
    """Supprime tous les salons et catégories existants."""
    for channel in guild.channels:
        try:
            await channel.delete()
        except Exception:
            pass

async def create_roles(guild: discord.Guild) -> dict:
    """Crée tous les rôles et retourne un dict nom→rôle."""
    roles = {}

    role_definitions = [
        # (nom, couleur_hex, hoist, mentionnable)
        ("👑 Arkian",              0xFFD700, True,  False),
        ("🛡️ Modérateur",          0xFF4444, True,  True),
        ("⭐ VIP Trading Master",   0x9B59B6, True,  True),
        ("🎓 Coaching",             0x3498DB, True,  True),
        ("✅ Membre Vérifié",       0x2ECC71, False, False),
        ("🔰 Nouveau Membre",       0x95A5A6, False, False),
        # Rôles marchés
        ("📈 Forex Trader",         0x1ABC9C, False, False),
        ("🪙 Crypto Trader",        0xF39C12, False, False),
        ("📊 Actions/Bourse",       0xE74C3C, False, False),
        ("📉 Indices Trader",       0x8E44AD, False, False),
        ("🏅 Matières Premières",   0xD35400, False, False),
        # Rôles niveau XP (attribués par MEE6)
        ("🥉 Apprenti Trader",      0xCD7F32, True,  False),
        ("🥈 Trader Confirmé",      0xC0C0C0, True,  False),
        ("🥇 Trader Expert",        0xFFD700, True,  False),
        ("💎 Trader Elite",         0x00FFFF, True,  False),
        ("👑 Légende du Trading",   0xFF69B4, True,  False),
    ]

    for name, color, hoist, mentionable in role_definitions:
        role = await guild.create_role(
            name=name,
            color=discord.Color(color),
            hoist=hoist,
            mentionable=mentionable
        )
        roles[name] = role
        print(f"  ✔ Rôle créé : {name}")
        await asyncio.sleep(0.3)

    return roles


async def build_overwrites(guild, roles, access="public", extra_allow=None):
    """
    Construit les permission overwrites.
    access: 'public' | 'verified' | 'vip' | 'coaching' | 'admin'
    """
    everyone = guild.default_role
    verified  = roles.get("✅ Membre Vérifié")
    vip       = roles.get("⭐ VIP Trading Master")
    coaching  = roles.get("🎓 Coaching")
    mod       = roles.get("🛡️ Modérateur")
    owner     = roles.get("👑 Arkian")

    # Par défaut tout le monde ne voit rien
    ow = {everyone: discord.PermissionOverwrite(view_channel=False)}

    if access == "public":
        ow[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    elif access == "readonly":
        ow[everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=False)

    elif access == "verified":
        ow[everyone]  = discord.PermissionOverwrite(view_channel=False)
        if verified:
            ow[verified] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    elif access == "verified_readonly":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if verified:
            ow[verified] = discord.PermissionOverwrite(view_channel=True, send_messages=False)

    elif access == "vip":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if vip:
            ow[vip] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    elif access == "vip_readonly":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if vip:
            ow[vip] = discord.PermissionOverwrite(view_channel=True, send_messages=False)

    elif access == "coaching":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)
        if coaching:
            ow[coaching] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    elif access == "admin":
        ow[everyone] = discord.PermissionOverwrite(view_channel=False)

    # Les mods et owner voient toujours tout
    for r in [mod, owner]:
        if r:
            ow[r] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_messages=True,
                manage_channels=True
            )

    if extra_allow:
        for role_name in extra_allow:
            r = roles.get(role_name)
            if r:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

    return ow


async def create_structure(guild: discord.Guild, roles: dict):
    """Crée toutes les catégories et leurs salons."""

    # ── 1. ACCUEIL ────────────────────────────────────────────────────────────
    cat = await guild.create_category("📌 ACCUEIL")
    channels_def = [
        ("📋・règles",        "text",  "readonly"),
        ("👋・bienvenue",     "text",  "readonly"),
        ("🎯・présentation",  "text",  "public"),
        ("📢・annonces",      "text",  "readonly"),
        ("🗺️・guide-serveur", "text",  "readonly"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 2. VÉRIFICATION & RÔLES ───────────────────────────────────────────────
    cat = await guild.create_category("✅ VÉRIFICATION & RÔLES")
    channels_def = [
        ("✅・vérification",   "text", "public"),
        ("🎭・choix-rôles",    "text", "verified"),
        ("📊・niveau-trading", "text", "verified"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 3. INFO ARKIAN ────────────────────────────────────────────────────────
    cat = await guild.create_category("🌟 INFO ARKIAN")
    channels_def = [
        ("🌟・présentation-arkian", "text", "readonly"),
        ("📺・youtube",             "text", "readonly"),
        ("💰・les-paiements",       "text", "readonly"),
        ("🔔・live-alerte",         "text", "readonly"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 4. ÉDUCATION GRATUITE ─────────────────────────────────────────────────
    cat = await guild.create_category("📚 ÉDUCATION GRATUITE")
    channels_def = [
        ("📚・ressources-gratuites", "text", "readonly"),
        ("🧠・info-macro",           "text", "verified"),
        ("💬・discussion-générale",  "text", "verified"),
        ("❓・questions-débutants",  "forum","verified"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 5. ACTIFS À TRADE (Membre vérifié) ───────────────────────────────────
    cat = await guild.create_category("📈 ACTIFS À TRADE")
    channels_def = [
        ("📈・forex",              "text", "verified"),
        ("📉・indices",            "text", "verified"),
        ("🏅・matières-premières", "text", "verified"),
        ("🪙・cryptos",            "text", "verified"),
        ("📊・actions-bourse",     "text", "verified"),
        ("⚡・signaux-gratuits",   "text", "verified"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 6. TRADING MASTER VIP ────────────────────────────────────────────────
    cat = await guild.create_category("⭐ TRADING MASTER VIP")
    channels_def = [
        ("🗓️・plans-de-la-semaine", "text", "vip_readonly"),
        ("📣・annonces-vip",        "text", "vip_readonly"),
        ("📍・mes-positions",       "text", "vip_readonly"),
        ("📆・semaine-plans",       "text", "vip"),
        ("💎・signaux-vip",         "text", "vip_readonly"),
        ("🔒・master-discussions",  "text", "vip"),
        ("🎓・éducatif-premium",    "text", "vip_readonly"),
        ("📋・journal-de-trade",    "text", "vip"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 7. COMMUNAUTÉ ─────────────────────────────────────────────────────────
    cat = await guild.create_category("🏆 COMMUNAUTÉ")
    channels_def = [
        ("🏆・classement",      "text", "verified"),
        ("🎉・récompenses",     "text", "readonly"),
        ("🤝・partenariats",    "text", "readonly"),
        ("📸・résultats-trades","text", "verified"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 8. COACHING ───────────────────────────────────────────────────────────
    cat = await guild.create_category("🎓 COACHING")
    channels_def = [
        ("📅・réservation",   "text",  "coaching"),
        ("🎙️・coaching-vocal","voice", "coaching"),
        ("📝・suivi-élèves",  "text",  "coaching"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 9. VOCAL ──────────────────────────────────────────────────────────────
    cat = await guild.create_category("🔊 VOCAL")
    channels_def = [
        ("🔊・général",       "voice", "verified"),
        ("📡・live-trading",  "voice", "verified"),
        ("🎓・formation-live","voice", "verified"),
        ("🤫・lounge-vip",   "voice", "vip"),
    ]
    await create_channels(guild, cat, channels_def, roles)

    # ── 10. LOGS & ADMIN (invisible membres) ──────────────────────────────────
    cat = await guild.create_category("🔧 LOGS & ADMIN")
    channels_def = [
        ("🔧・bot-logs",     "text", "admin"),
        ("🚨・mod-logs",     "text", "admin"),
        ("📊・stats-serveur","text", "admin"),
        ("👮・staff-chat",   "text", "admin"),
    ]
    await create_channels(guild, cat, channels_def, roles)


async def create_channels(guild, category, channels_def, roles):
    """Crée une liste de salons dans une catégorie."""
    for name, kind, access in channels_def:
        ow = await build_overwrites(guild, roles, access)
        try:
            if kind == "voice":
                ch = await guild.create_voice_channel(name, category=category, overwrites=ow)
            elif kind == "forum":
                ch = await guild.create_forum_channel(name, category=category, overwrites=ow)
            else:
                slowmode = 5 if access in ("public", "verified") else 0
                ch = await guild.create_text_channel(
                    name, category=category, overwrites=ow, slowmode_delay=slowmode
                )
            print(f"    ✔ #{name}")
        except Exception as e:
            print(f"    ✘ #{name} — {e}")
        await asyncio.sleep(0.4)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"\n🤖 Bot connecté : {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Serveur introuvable. Vérifie GUILD_ID et que le bot est bien invité.")
        await client.close()
        return

    print(f"🎯 Serveur cible : {guild.name}\n")

    print("🗑️  Suppression des salons existants...")
    await delete_existing(guild)

    print("\n🎭 Création des rôles...")
    roles = await create_roles(guild)

    print("\n🏗️  Construction de la structure...")
    await create_structure(guild, roles)

    print("\n✅ Configuration terminée !")
    print("\n📋 Prochaines étapes manuelles :")
    print("   1. Invite Carl-bot  → configure bouton d'acceptation des règles")
    print("   2. Invite MEE6      → configure les paliers XP et rôles automatiques")
    print("   3. Invite Ticket Tool → configure les tickets VIP/coaching")
    print("   4. Invite Statbot   → configure les compteurs membres")
    print("   5. Invite Streamcord → configure les alertes YouTube/Twitch")

    await client.close()


if __name__ == "__main__":
    if TOKEN == "TON_TOKEN_ICI":
        print("⚠️  Configure ton TOKEN et GUILD_ID avant de lancer le script.")
        print("   Option 1 : variables d'environnement")
        print("     export DISCORD_TOKEN='ton_token'")
        print("     export DISCORD_GUILD_ID='ton_guild_id'")
        print("   Option 2 : modifie directement les constantes en haut du fichier")
    else:
        client.run(TOKEN)
