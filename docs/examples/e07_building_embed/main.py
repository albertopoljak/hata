from hata import Client, Embed, ReuAsyncIO

TOKEN = ''

Sakuya = Client(TOKEN)

@Sakuya.events
async def message_create(client, message):
    if message.content == '!hello':
        
        # This example will create a message with an embed that has a title, description, three fields, and a footer.
        embed = Embed(
            'This is a title',
            'This is a description',
        ).add_image(
            'attachment://ferris_eyes.png'
        ).add_field(
            'This is the first field name',
            'This is a field value',
            inline = True,
        ).add_field(
            'This is the second field name',
            'Both of these fields are inline',
        ).add_field(
            'This is the third field',
            'This is not an inline field',
        ).footer(
            'This is a footer',
        )
        
        # Using reusable asynchronous input / output.
        #
        # Using asynchronous io-s is important, since the program runs in asynchronous environment, and using blocking
        # io just ones, takes away enough time to handle thousands of events.
        #
        # Requests sometimes fail for connection issues, or because the Discord servers derp out. At these case the
        # wrapper tries to repeat the request 5 times. This is when reusable io-s come to the picture.
        with (await ReuAsyncIO('flan.png')) as file:
            await client.message_create(message.channel, embed=embed, file=file)


@Sakuya.events
async def ready(client):
    print(f'{client:f} is connected!')


Sakuya.start()
