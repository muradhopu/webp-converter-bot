import logging
import os
import io
from PIL import Image
from telegram import Update, File
from telegram.ext import Application, CommandHandler,
MessageHandler, filters
# Enable logging
logging.basicConfig(
format="%(asctime)s - %(name)s - %(levelname)s - %
(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and
POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
# Bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
def convert_to_webp(image_bytes: bytes) -> bytes:
"""Converts an image from various formats to WebP."""
try:
img = Image.open(io.BytesIO(image_bytes))
if img.format == 'WEBP':
return image_bytes # Already WebP
output_buffer = io.BytesIO()
img.save(output_buffer, format="WEBP")
return output_buffer.getvalue()
except Exception as e:
logger.error(f"Error converting to WebP: {e}")
return None
def convert_from_webp(image_bytes: bytes) -> bytes:
"""Converts a WebP image to PNG."""
try:
img = Image.open(io.BytesIO(image_bytes))
if img.format != 'WEBP':
return image_bytes # Not WebP, return original
output_buffer = io.BytesIO()
img.save(output_buffer, format="PNG")
return output_buffer.getvalue()
except Exception as e:
logger.error(f"Error converting from WebP: {e}")
return None
async def start(update: Update, context) -> None:
"""Sends a welcome message when the command /start is
issued."""
welcome_message = (
"Hello! I'm a WebP Converter Bot. Send me an image
(as a photo or a document) "
"and I will convert it for you.\n\n"
"- If you send a WebP image, I'll convert it to
PNG.\n"
"- If you send a non-WebP image (like JPG, PNG,
etc.), I'll convert it to WebP."
)
await update.message.reply_text(welcome_message)
async def handle_image(update: Update, context) -> None:
"""Handles incoming images (photos and documents)."""
if update.message.photo:
file_id = update.message.photo[-1].file_id
file: File = await context.bot.get_file(file_id)
file_bytes = io.BytesIO()
await file.download_to_memory(file_bytes)
file_bytes.seek(0)
image_bytes = file_bytes.getvalue()
file_name = "image.jpg" # Default name for photos
elif update.message.document:
document = update.message.document
if not document.mime_type.startswith('image/'):
await update.message.reply_text("Please send an
image file.")
return
file_id = document.file_id
file_name = document.file_name
file: File = await context.bot.get_file(file_id)
file_bytes = io.BytesIO()
await file.download_to_memory(file_bytes)
file_bytes.seek(0)
image_bytes = file_bytes.getvalue()
else:
await update.message.reply_text("Please send an
image as a photo or a document.")
return
try:
# Determine if the image is WebP or not
img = Image.open(io.BytesIO(image_bytes))
is_webp = (img.format == 'WEBP')
img.close()
if is_webp:
converted_image_bytes =
convert_from_webp(image_bytes)
if converted_image_bytes:
output_filename =
os.path.splitext(file_name)[0] + ".png"
await
update.message.reply_document(document=io.BytesIO(converted_ima
filename=output_filename)
else:
await update.message.reply_text("Failed to
convert WebP to PNG.")
else:
converted_image_bytes =
convert_to_webp(image_bytes)
if converted_image_bytes:
output_filename =
os.path.splitext(file_name)[0] + ".webp"
await
update.message.reply_document(document=io.BytesIO(converted_ima
filename=output_filename)
else:
await update.message.reply_text("Failed to
convert image to WebP.")
except Exception as e:
logger.error(f"Error processing image: {e}")
await update.message.reply_text("An error occurred
while processing your image. Please try again.")
def main() -> None:
"""Start the bot."""
application =
Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO |
filters.Document.IMAGE, handle_image))
logger.info("Bot started. Listening for updates...")
application.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == "__main__":
main()
