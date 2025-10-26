import html
import sys
import os

import aiohttp
import git
from pyrogram.types import Message

from app import BOT, bot

# --- CONFIGURATION ---
# IMPORTANT: Change these values to match your project!
UPSTREAM_REPO_URL = "https://github.com/R0Xofficial/PlainUB-Extras"  # <-- Paste your repository URL here
BRANCH = "main"  # Change to "master" if that is your main branch

# --- Helper Functions ---

async def get_latest_commit_info(session, repo_url, branch):
    api_url = repo_url.replace("github.com", "api.github.com/repos")
    commits_url = f"{api_url}/commits/{branch}"
    try:
        async with session.get(commits_url) as response:
            response.raise_for_status()
            data = await response.json()
            return {
                "hash": data["sha"],
                "message": data["commit"]["message"].split('\n')[0],
                "author": data["commit"]["author"]["name"],
            }
    except (aiohttp.ClientError, KeyError, IndexError):
        return None

async def get_changelog(session, repo_url, old_hash, new_hash):
    api_url = repo_url.replace("github.com", "api.github.com/repos")
    compare_url = f"{api_url}/compare/{old_hash}...{new_hash}"
    try:
        async with session.get(compare_url) as response:
            response.raise_for_status()
            data = await response.json()
            if "commits" not in data or not data["commits"]:
                return "Could not retrieve new commits or comparison failed."

            changelog = ""
            commits_to_show = data["commits"][:10]
            for commit in reversed(commits_to_show):
                commit_hash = commit['sha'][:7]
                message = html.escape(commit['commit']['message'].split('\n')[0])
                author = commit['commit']['author']['name']
                changelog += f"  - `[{commit_hash}]`: {message} - *by {author}*\n"
            
            if len(data["commits"]) > 10:
                changelog += f"\n*...and {len(data['commits']) - 10} more commits.*"
            return changelog
    except Exception:
        return "Failed to fetch the changelog."

# --- Main Command Handler ---

@bot.add_cmd(cmd="modgrade")
async def check_update_handler(bot: BOT, message: Message):
    progress_msg = await message.reply("`Checking for updates...`")

    try:
        repo = git.Repo(search_parent_directories=True)
        local_commit_hash = repo.head.commit.hexsha
    except git.InvalidGitRepositoryError:
        return await progress_msg.edit("`ERROR: This script is not running in a Git repository.`")
    except Exception as e:
        return await progress_msg.edit(f"`ERROR checking local version: {e}`")

    async with aiohttp.ClientSession() as session:
        remote_commit = await get_latest_commit_info(session, UPSTREAM_REPO_URL, BRANCH)

    if not remote_commit:
        return await progress_msg.edit("`Could not fetch update info from GitHub. Please try again later.`")

    remote_commit_hash = remote_commit["hash"]

    if local_commit_hash == remote_commit_hash:
        response_text = (
            "**✅ Your bot is up-to-date!**\n\n"
            f"**Installed Version:**\n"
            f"  - `{local_commit_hash[:7]}`"
        )
        return await progress_msg.edit(response_text)

    response_text = (
        "**⚠️ A new update is available!**\n\n"
        f"**Your Version (Local):**\n"
        f"  - `{local_commit_hash[:7]}`\n\n"
        f"**Latest Version (Remote):**\n"
        f"  - `{remote_commit_hash[:7]}`\n\n"
        "**Changelog:**\n"
    )

    async with aiohttp.ClientSession() as session:
        changelog = await get_changelog(session, local_commit_hash, remote_commit_hash)
    
    response_text += changelog
    response_text += "\n\nTo update, please use your bot's designated update command."
    
    await progress_msg.edit(response_text)
