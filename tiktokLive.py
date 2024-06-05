import csv
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent


tikTokUser = input("Input the TikTok ID starting with @ sign: ")

# "@oxxalate"
# Create the client
client: TikTokLiveClient = TikTokLiveClient(unique_id=tikTokUser)

# Define field names for CSV
fieldnames = ['Song Name', 'Artist']

# Listen to an event with a decorator!
@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id} (Room ID: {client.room_id})")

@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    print(f"{event.user.nickname} said: {event.comment}")

    # Extract song name and artist from the comment
    if "SONG:" in event.comment:
        comment_parts = event.comment.split("SONG:")[1].strip().split(' by ')
        if len(comment_parts) == 2:
            song_name = comment_parts[0].strip()
            artist = comment_parts[1].strip()

            # Write song details to CSV in "Song Name, Artist" format
            with open('song_details.csv', 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({'Song Name': song_name, 'Artist': artist})

client.add_listener(CommentEvent, on_comment)

if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
