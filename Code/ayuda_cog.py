import discord
import datetime
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(ayuda_cog(bot))


class ayuda_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embedOrange = 0xeab148
        self.embedDarkPink = 0x7d3243

    def infoEmbedGen(self, name):
        embed = discord.Embed(
            title="¡Hola!",
            description=f"""
            ¡Hola, soy {name}! Puedes escribir cualquier comando después de escribir mi prefijo **`'{self.bot.command_prefix}'`** para activarlos. Utiliza **`!ayuda`** para ver algunas opciones de comando.

            Aquí tienes un enlace a mi [página web](https://www.lunaespindola.dev) si quisieras echarle un vistazo!""",
            colour=self.embedOrange
        )
        return embed

    def errorEmbedGen(self, error):
        embed = discord.Embed(
            title="ERROR :(",
            description="Hubo un error. Probablemente puedas seguir usando el bot tal como está, o, por si acaso, puedes pedirle a tu administrador de servidor que use !reiniciar para reiniciar el bot.\n\nError:\n**`" +
            str(error) + "`**",
            colour=self.embedDarkPink
        )
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print(print("[" + datetime.time.now() + "] " + str(error)))
        await ctx.send(embed=self.errorEmbedGen(error))

    @ commands.Cog.listener()
    async def on_ready(self):
        sendToChannels = []
        botNames = {}
        for guild in self.bot.guilds:
            channel = guild.text_channels[0]
            sendToChannels.append(channel)
            botMember = await guild.fetch_member(975410595576840272)
            nickname = botMember.nick
            if nickname == None:
                nickname = botMember.name
            botNames[guild.id] = nickname

    @ commands.command(
        name="ayuda",
        aliases=["b"],
        help="""
            (nombre_de_comando)
            Proporciona una descripción de todos los comandos o una descripción más detallada de un comando de entrada
            Da una descripción de un comando especificado (opcional). Si no se especifica ningún comando, entonces da una descripción menos detallada de todos los comandos.
            """
    )
    
    async def ayuda(self, ctx, arg=""):
        helpCog = self.bot.get_cog('ayuda_cog')
        musicCog = self.bot.get_cog('music_cog')
        commands = helpCog.get_commands() + musicCog.get_commands()
        if arg != "":
            command = None
            for i, c in enumerate(commands):
                if c.name == arg:
                    command = commands[i]
            if command == None:
                await ctx.send("Ese no es el nombre de un comando disponible.")
                return

            arguments = command.help.split("\n")[0]
            longHelp = command.help.split("\n")[2]
            aliases = ""
            for a in command.aliases:
                aliases += f"!{a}, "
            aliases = aliases.rstrip(", ")
            commandsEmbed = discord.Embed(
                title=f"!{command.name} Información de Comando",
                description=f"""
                Argumentos: **`{arguments}`**
                {longHelp}

                Alias: **`{aliases}`**
                """,
                colour=self.embedOrange
            )

        else:
            commandDescription = ""
            for c in commands:
                arguments = c.help.split("\n")[0]
                shortHelp = c.help.split("\n")[1]
                commandDescription += f"**`!{c.name} {arguments}`** - {shortHelp}\n"
            commandsEmbed = discord.Embed(
                title="Lista de Comandos",
                description=commandDescription,
                colour=self.embedOrange
            )

        commandKey = """
            **`Prefijo de Comando`** - '!'

            **`!comando <>`** - No se requieren argumentos
            **`!comando ()`** - Argumento opcional
            **`!comando []`** - Argumento requerido
            **`!comando [arg]`** - 'arg' especifica el tipo de argumento (por ejemplo, "url" o "palabras clave")
            **`!comando (esto || eso)`** - Opciones entre entradas mutuamente excluyentes (esto o eso)
        """

        keyEmbed = discord.Embed(
            title="Clave",
            description=commandKey,
            colour=self.embedOrange
        )
        await ctx.send(embed=commandsEmbed)
        await ctx.send(embed=keyEmbed)
        
    @ commands.command(
        name="reiniciar",
        aliases=["ri"],
        help="""
            <>
            Reinicia completamente el bot.
            Da un reinicio completo del bot. Este comando solo puede ser llamado por el propietario del servidor.
            """
    )
    async def reiniciar(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            await ctx.send("¡Reiniciando la aplicación ahora!")
            await self.bot.close()
        else:
            await ctx.send("No tienes permisos adecuados para reiniciarme.")
            
    @commands.command(
        name='inf',
        aliases=[],
        help="""
            <>
            Da información sobre el bot
            Da información sobre el bot
            """
    )
    async def info(self, ctx):
        await ctx.send(embed=self.infoEmbedGen("Bobbert"))
        