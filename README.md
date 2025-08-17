# Facebook YouTube Kirtan Pipeline

This project contains an automated pipeline to fetch the latest Kirtan video from a specified YouTube channel, translate its transcript, and post it to a Facebook page.

## Description

The core logic is in `main.py`. The pipeline performs the following steps:
1.  **Fetches Latest YouTube Video**: Identifies the most recent video from a target YouTube channel.
2.  **Gets Video Transcript**: Retrieves the auto-generated or manually uploaded transcript for the video.
3.  **Translates Text**: Translates the transcript into English using Google Translate.
4.  **Posts to Facebook**: Composes a message with the translated text and posts it to a target Facebook page.

The pipeline is designed to be run automatically, for instance, on a weekly schedule using GitHub Actions.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/facebook-youtube-kirtan-pipeline.git
    cd facebook-youtube-kirtan-pipeline
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Configure API Keys and IDs:**
    Open `main.py` and replace the placeholder values with your actual credentials.

    ### API Key Placeholders

    You need to obtain the following credentials:

    *   **`FACEBOOK_PAGE_ID`**: The ID of the Facebook Page you want to post to.
    *   **`FACEBOOK_APP_ID`**: The ID of your Facebook App.
    *   **`FACEBOOK_APP_SECRET`**: The secret for your Facebook App.
    *   **`FACEBOOK_ACCESS_TOKEN`**: A long-lived Page Access Token with `pages_read_engagement` and `pages_manage_posts` permissions.
    *   **`YOUTUBE_API_KEY`**: Your Google Cloud API Key with the YouTube Data API v3 enabled.
    *   **`YOUTUBE_CHANNEL_ID`**: The ID of the YouTube channel you want to monitor.

    For production use (like in GitHub Actions), it is **strongly recommended** to use repository secrets instead of hardcoding these values.

## How to Run Locally

After setting up and configuring the API keys, you can run the pipeline manually:

```bash
python main.py
```

The script will print its progress to the console.

## Important Note on Human Review

**Automated translations are not always perfect.** The quality of the translation depends heavily on the clarity of the source audio and the complexity of the language.

The `main.py` script includes a conceptual "Human Review" step. In the current code, this is a simple `input()` prompt that pauses the script. Before deploying this in a fully automated way, you should implement a robust review process. For example:

*   The script could save the translated text to a file or a database.
*   A notification is sent to a human reviewer.
*   The reviewer checks and corrects the text.
*   A separate script or a manual trigger is used to publish the reviewed content.

**Auto-publishing without human review may lead to inaccurate or nonsensical content being posted.**

## Automation with GitHub Actions

This repository includes a GitHub Actions workflow in `.github/workflows/weekly.yml`. This workflow is configured to:
*   Run every Monday at 06:00 IST (00:30 UTC).
*   Set up a Python 3.10 environment.
*   Install the required dependencies.
*   Run the `main.py` script.

To make this work, you must add your API keys and tokens as secrets to your GitHub repository. The secrets should be named (for example) `FACEBOOK_ACCESS_TOKEN`, `YOUTUBE_API_KEY`, etc., and you would need to modify the `weekly.yml` file to pass them as environment variables to the script.
