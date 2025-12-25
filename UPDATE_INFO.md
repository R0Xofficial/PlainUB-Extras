# PlainUB-Extras — Update Info

This document provides additional information for updating the custom modules in your userbot.

## Overview

These modules are installed in the `ubot/app/modules` directory of your userbot. Whenever an update is released, there might be changes in dependencies that require reinstalling the requirements file.

## When to Reinstall Requirements

You should reinstall the dependencies if you see a warning, errors in host console or when the userbot off on its own.

This usually happens when:
- New features are added
- Existing modules are updated
- Dependencies are updated

## How to Reinstall Requirements

Run the following command in your userbot's environment:

```bash
pip install -r ~/ubot/app/modules/requirements.txt
```

Last Update: 2025-12-25
