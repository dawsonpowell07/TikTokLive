import csv
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent, ConnectEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="patrick_ali2023")

@client.on("connect")
async def on_connect(_: ConnectEvent):
    print("Connected to Room ID:", client.room_id)

async def on_comment(event: CommentEvent):
    print(f"{event.user.nickname} -> {event.comment}")
    
    # Extract song name and artist from the comment
    if "SONG:" in event.comment:
        comment_parts = event.comment.split("SONG:")[1].strip().split(' by ')
        if len(comment_parts) == 2:
            song_name = comment_parts[0].strip()
            artist = comment_parts[1].strip()

            # Defineç fieldnames
            fieldnames = ['Song Name', 'Artist']

            # Write song details to CSV in "Song Name, Artist" format
            with open('song_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({'Song Name': song_name, 'Artist': artist})



client.add_listener("comment", on_comment)

if __name__ == '__main__':
    client.run()
