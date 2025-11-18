import requests
import asyncio
import html
from pyrogram.types import LinkPreviewOptions, Message

ERROR_VISIBLE_DURATION = 8

def sync_get_releases(owner: str, repo: str) -> list:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.json()

async def get_android_versions(bot, message: Message, owner: str, repo: str, show_both: bool = False):
    display_name = repo
    if repo == "KernelSU" and owner == "KernelSU-Next":
        display_name = "KernelSU-Next"

    progress_message = await message.reply(f"<code>Checking for latest {display_name} releases...</code>")
    
    try:
        releases_data = await asyncio.to_thread(sync_get_releases, owner, repo)
        
        if not releases_data:
            raise ValueError("No releases found for this repository.")

        final_text = [f"<b>📦 Latest {display_name} Releases:</b>"]

        if show_both:
            stable = next((r for r in releases_data if not r['prerelease']), None)
            prerelease = next((r for r in releases_data if r['prerelease']), None)
            
            if not stable and not prerelease:
                raise ValueError("Could not find any release.")
            
            if stable:
                final_text.append(f"\n<b>Stable:</b> <a href='{stable['html_url']}'>{stable['tag_name']}</a>\n└ <code>{stable['published_at'].split('T')[0]}</code>")
            if prerelease:
                final_text.append(f"\n<b>Pre-release:</b> <a href='{prerelease['html_url']}'>{prerelease['tag_name']}</a>\n└ <code>{prerelease['published_at'].split('T')[0]}</code>")
        else:
            latest = releases_data[0]
            final_text.append(f"\n<b>Latest:</b> <a href='{latest['html_url']}'>{latest['tag_name']}</a>\n└ <code>{latest['published_at'].split('T')[0]}</code>")
            
        await progress_message.edit(
            "\n".join(final_text),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    except Exception as e:
        error_text = f"<b>An error occurred:</b>\n<code>{html.escape(str(e))}</code>"
        await progress_message.edit(error_text)
        await asyncio.sleep(ERROR_VISIBLE_DURATION)
        await progress_message.delete()
