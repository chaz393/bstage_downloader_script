import asyncio
import discord
import subprocess
import requests
import os
from discord import app_commands
from discord import Interaction

# put your bot token here
BOT_TOKEN = ""

# this is used for development to sync the application commands to a single server
# set to guild = None for normal operation
guild = None
client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    await tree.sync(guild=guild)


@tree.command(name="ping", description="pong", guild=guild)
async def command_ping(interaction: Interaction):
    await interaction.response.send_message("pong")


@tree.command(name="get-post", description="gets bstage post and sends the media", guild=guild)
async def command_get_post(interaction: Interaction, post_url: str):
    print(f"downloading: {post_url} in #{interaction.channel_id}")
    await interaction.response.defer()
    post_response = requests.get(post_url)
    if post_response.status_code != 200:
        print(f"error downloading {post_url}")
        await interaction.edit_original_response(content=f"There was an error getting the post")
        return
    if "\"video\":{\"id\"" in str(post_response.content):
        print("downloading video")
        await download_video_post(post_response, post_url, interaction)
    elif "\"images\":[" in str(post_response.content):
        print("downloading photo")
        await download_photo_post(post_response, post_url, interaction)
    else:
        print("text post, skipping")


async def download_photo_post(response, post_url, interaction: Interaction):
    if response.status_code != 200:
        print(f"error downloading {post_url}")
        await interaction.edit_original_response(content=f"There was an error getting the post")
        return

    post_id = str(response.text).split("\"post\":{\"id\":\"")[1].split("\"")[0]
    author = str(response.text).split("\"nickname\":\"")[1].split("\"")[0]
    post_text = str(response.text).split("\"body\":\"")[1].split("\"")[0]

    print(post_id)
    print(author)
    print(post_text)

    output_folder = f"downloads/{author}/{post_id}" \
        .format(author=author, post_id=post_id)
    os.makedirs(output_folder, exist_ok=True)

    file_paths = []
    image_urls = str(response.content).split("\"images\":[")[1].split("]")[0]
    for image_url in image_urls.split(","):
        image_url = image_url.split("\"")[1]
        media_id = image_url.split("/")[-2]
        full_path = output_folder + f"/{media_id}.jpeg".format(media_id=media_id)

        print(image_url)
        print(media_id)
        print(full_path)
        if os.path.isfile(full_path):
            print(f"file exists, skipping download: {full_path}")
        else:
            print("download the thing")
            image_response = requests.get(image_url)
            if image_response.status_code != 200:
                print(f"error downloading image {image_url}")
            with open(full_path, 'wb') as file:
                file.write(image_response.content)
                file.close()
        file_paths.append(full_path)
        await send_discord_response(interaction, post_text, author, file_paths)


async def download_video_post(response, post_url, interaction: Interaction):
    if response.status_code != 200:
        print(f"error downloading {post_url}")
        await interaction.edit_original_response(content=f"There was an error getting the post")
        return

    post_id = str(response.text).split("\"post\":{\"id\":\"")[1].split("\"")[0]
    media_id = str(response.text).split("\"video\":{\"id\":\"")[1].split("\"")[0]
    author = str(response.text).split("\"nickname\":\"")[1].split("\"")[0]
    post_text = str(response.text).split("\"body\":\"")[1].split("\"")[0]
    m3u8_url = str(response.text).split("\"dashPath\":\"")[1].split("\"")[0]

    print(post_id)
    print(media_id)
    print(author)
    print(post_text)
    print(m3u8_url)

    output_path = f"downloads/{author}/{post_id}/{media_id}.mp4"\
        .format(author=author, post_id=post_id, media_id=media_id)
    print(output_path)
    if os.path.isfile(output_path):
        print(f"file exists, skipping download: {output_path}")
    else:
        print("download the thing")
        subprocess.run(["yt-dlp", "-o", output_path, m3u8_url])
    await send_discord_response(interaction, post_text, author, [output_path])


async def send_discord_response(interaction: Interaction, post_text: str, author: str, file_paths: []):
    files = []
    for file_path in file_paths:
        files.append(discord.File(file_path))

    print(f"sending message {post_text} in #{interaction.channel_id}")
    await interaction.edit_original_response(content=build_response_body(author, post_text), attachments=files)


def build_response_body(author, post_text):
    return f"Pixy bstage post by {author}: \n\n{post_text}"


async def start_bot():
    await client.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(start_bot())
