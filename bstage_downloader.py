import os
import sys
import requests
import subprocess


def download_photo(response):
    if response.status_code != 200:
        exit(1)

    post_id = str(response.text).split("\"post\":{\"id\":\"")[1].split("\"")[0]
    author = str(response.text).split("\"nickname\":\"")[1].split("\"")[0]
    post_text = str(response.text).split("\"body\":\"")[1].split("\"")[0]

    print(post_id)
    print(author)
    print(post_text)

    output_folder = f"downloads/{author}/{post_id}" \
        .format(author=author, post_id=post_id)
    os.makedirs(output_folder, exist_ok=True)

    created_embed = False
    image_urls = str(response.content).split("\"images\":[")[1].split("]")[0]
    for image_url in image_urls.split(","):
        image_url = image_url.split("\"")[1]
        media_id = image_url.split("/")[-2]
        full_path = output_folder + f"/{media_id}.jpeg".format(media_id=media_id)

        print(image_url)
        print(media_id)
        print(full_path)

        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            exit(1)
        with open(full_path, 'wb') as file:
            file.write(image_response.content)
            file.close()


def download_video(response):
    if response.status_code != 200:
        exit(1)
    post_id = str(response.text).split("\"post\":{\"id\":\"")[1].split("\"")[0]
    media_id = str(response.text).split("\"video\":{\"id\":\"")[1].split("\"")[0]
    author = str(response.text).split("\"nickname\":\"")[1].split("\"")[0]
    m3u8_url = str(response.text).split("\"dashPath\":\"")[1].split("\"")[0]

    print(post_id)
    print(media_id)
    print(author)
    print(m3u8_url)

    output_path = f"downloads/{author}/{post_id}/{media_id}.%(ext)s"\
        .format(author=author, post_id=post_id, media_id=media_id)
    print(output_path)
    subprocess.run(["yt-dlp", "-o", output_path, m3u8_url])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("please provide only one argument, the post url")
        exit(1)
    else:
        post_response = requests.get(sys.argv[1])
        if post_response.status_code != 200:
            exit(1)
        if "\"video\":{\"id\"" in str(post_response.content):
            print("downloading video")
            download_video(post_response)
        elif "\"images\":[" in str(post_response.content):
            print("downloading photo")
            download_photo(post_response)
        else:
            print("text post, skipping")
