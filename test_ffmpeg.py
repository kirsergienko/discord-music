import discord
print("discord version:", discord.__version__)
kwargs = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}
try:
    source = discord.FFmpegPCMAudio("test.mp3", **kwargs)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
