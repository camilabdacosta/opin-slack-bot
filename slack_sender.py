import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
from typing import Optional # <--- ESSENCIAL: Importar Optional para type hinting em Python < 3.10

# Configure logging (optional but good practice)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration --- 
# IMPORTANT: Set the SLACK_BOT_TOKEN environment variable before running.
# Ensure the bot has the following scopes in Slack App settings:
# - files:write (to upload the audio file)
# - chat:write (to post messages)
# - channels:read (to find public channel IDs by name)
# - groups:read (to find private channel IDs by name)
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
TARGET_CHANNEL_NAME = "podcastopin" # Canal fixo no código, ignorando variável de ambiente.

# --- LINHA DE DEBBUGING ADICIONADA ---
print(f"DEBUG: TARGET_CHANNEL_NAME lido: '{TARGET_CHANNEL_NAME}'")
# --- FIM DA LINHA DE DEBUGGING ---


def get_channel_id(client: WebClient, channel_name: str) -> Optional[str]: # <--- CORRIGIDO: str | None para Optional[str]
    """Finds the Slack Channel ID for a given channel name."""
    logger.info(f"Attempting to find Channel ID for '{channel_name}'...")
    try:
        # Iterate through relevant channel types the bot might be in or have access to read
        for channel_type in ["public_channel", "private_channel"]:
            logger.debug(f"Checking channels of type: {channel_type}")
            # Note: conversations.list requires channels:read (public) or groups:read (private) scopes.
            response = client.conversations_list(types=channel_type, limit=1000) # Increase limit if many channels
            channels = response.get("channels", [])
            for channel in channels:
                if channel.get("name") == channel_name:
                    channel_id = channel.get("id")
                    logger.info(f"Found Channel ID: {channel_id} for name '{channel_name}'")
                    return channel_id
        logger.error(f"Channel '{channel_name}' not found among the bot's accessible channels.")
        logger.error("Ensure the bot is invited OR has necessary read permissions (channels:read/groups:read).")
        return None
    except SlackApiError as e:
        # Check for missing scope error specifically
        if e.response.get("error") == "missing_scope":
            needed_scope = e.response.get("needed", "channels:read or groups:read")
            logger.error(f"Error fetching channel list: Missing required Slack scope: {needed_scope}")
            logger.error("Please add the required scope(s) to your Slack App configuration.")
        else:
            logger.error(f"Error fetching channel list from Slack: {e.response['error']}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred while fetching channel ID: {e}")
        return None

def send_to_slack(audio_file_path, bulletin_number, initial_comment):
    """
    Uploads an audio file and posts a message to a Slack channel using its ID.

    Args:
        audio_file_path (str): The absolute path to the audio file to upload.
        bulletin_number (str): The bulletin number (extracted previously).
        initial_comment (str): The initial message text to post with the file.
                               This will be formatted with the bulletin number.

    Returns:
        bool: True if successful, False otherwise.
    """
    logger.info(f"--- Sending to Slack Channel Name: {TARGET_CHANNEL_NAME} ---")

    if not SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN environment variable not set.")
        logger.error("Please create a Slack App, get the Bot Token (xoxb-...), and set the environment variable.")
        return False

    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file not found at {audio_file_path}")
        return False

    client = WebClient(token=SLACK_BOT_TOKEN)

    # --- Get Channel ID --- 
    channel_id = get_channel_id(client, TARGET_CHANNEL_NAME)
    if not channel_id:
        logger.error("Failed to find Channel ID. Cannot send message.")
        return False
    # ---

    # --- CORREÇÃO AQUI: Use initial_comment diretamente, pois já vem formatado do main.py ---
    # formatted_comment = initial_comment.format(numero_boletim=bulletin_number) # LINHA REMOVIDA/MODIFICADA
    formatted_comment = initial_comment # Use a string já formatada

    try:
        logger.info(f"Uploading audio file: {audio_file_path} to Channel ID: {channel_id}...")
        response = client.files_upload_v2(
            channel=channel_id, # Use Channel ID here
            file=audio_file_path,
            initial_comment=formatted_comment, # Use a string já formatada aqui
            title=f"Resumo Boletim Open Insurance {bulletin_number}" # O título do arquivo ainda usa o numero_boletim
        )
        logger.info("File uploaded successfully.")
        return True

    except SlackApiError as e:
        logger.error(f"Error uploading file or sending message to Slack (using Channel ID {channel_id}): {e.response['error']}")
        # More detailed error info can be found in e.response
        # logger.error(f"Full Slack API Error Response: {e.response}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred during Slack interaction: {e}")
        return False

# Example usage (for testing)
if __name__ == "__main__":
    # Create a dummy audio file for testing if it doesn't exist
    dummy_audio = "/home/ubuntu/opin_slack_bot/dummy_audio.mp3"
    if not os.path.exists(dummy_audio):
        try:
            with open(dummy_audio, "w") as f:
                f.write("dummy audio content")
            logger.info(f"Created dummy audio file: {dummy_audio}")
        except Exception as e:
            logger.exception(f"Could not create dummy audio file: {e}")

    # --- IMPORTANT --- 
    # Ensure SLACK_BOT_TOKEN is set as an environment variable before running this test.
    # Ensure the bot is invited to the channel named 'podcastopin' OR has read permissions.
    # Ensure the bot has scopes: files:write, chat:write, channels:read, groups:read
    # --- 

    if SLACK_BOT_TOKEN:
        logger.info("\n--- Testing Slack Sender --- ")
        test_bulletin_num = "XYZ-Test"
        test_comment = "Olá aqui é BotOpin e gostaria de compartilhar o resumo do Boletim Numero {numero_boletim}"
        success = send_to_slack(dummy_audio, test_bulletin_num, test_comment)

        if success:
            logger.info("\nSlack sender test completed successfully (check the channel!).")
        else:
            logger.error("\nSlack sender test failed.")
    else:
        logger.warning("\nSkipping Slack sender test because SLACK_BOT_TOKEN is not set.")
