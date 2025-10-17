# Plain-UB Extras

Repository **"PlainUB-Extras"** is a collection of additional modules and features designed for use with [plain-ub](https://github.com/thedragonsinn/plain-ub) — A simple Telegram User-Bot. These scripts extend the functionality of the bot with custom commands and tools.

## ⚙️ How to Use

### ✅ Automatic Method (Recommended) (Need Docker)

1. Fork or clone this repository.
2. In your docker `config.env` file, add or modify the following line to point to your fork or this repository directly:

   ```env
   EXTRA_MODULES_REPO=https://github.com/R0Xofficial/PlainUB-Extras
   ```

3. Deploy or restart your bot. The modules will be automatically loaded from the external repository.

4. To **update the modules** from the external repository (your fork), simply use the following command in the chat:

   ```
   .extupdate
   ```

---

### ⚙️ Manual Deployment (Alternative)

If you're deploying manually (without `EXTRA_MODULES_REPO`), you can also install the modules this way:

1. Go to the `app` folder in your Plain-UB directory:

   ```bash
   cd app
   ```

2. Create a new folder named `modules` if it doesn't already exist:

   ```bash
   mkdir modules
   ```

3. Clone this repository into the `modules` folder:

   ```bash
   git clone https://github.com/R0Xofficial/PlainUB-Extras modules
   ```

4. Restart your bot to load the modules.

5. To **update the modules** from the external repository (your fork), simply use the following command in the chat:

   ```
   .extupdate
   ```

---

## 🛠️ Extra Configuration

Some modules may require additional configuration, such as API keys or tokens. To configure them:

1. Copy the example config file:

   ```bash
   cp example-extra_config.env extra_config.py
   ```

2. Open `extra_config.py` in a text editor and fill in your own API keys or tokens as needed.

3. Restart your bot after saving the changes.

---

## 📦 Install Requirements

Some modules may require additional Python packages. To install all necessary dependencies from the `requirements.txt` file, run:

```bash
pip install -r requirements.txt
```

Make sure you're in the correct directory where the `requirements.txt` file is located, or provide the full path.

📄 **Note:**  
Some modules may require additional libraries that are not available via **pip**.  
In such cases, you need to install them using **pkg** (for example, in Termux):  

```bash
pkg install <package_name>
```
Example:

```bash
pkg install speedtest zbar pyzbar -y
```

---

## ❗ Disclaimer

> You are using these modules at **your own risk**.

I am **not responsible** for:
- incorrect or abusive usage of these modules,
- violations of Telegram's Terms of Service (ToS),
- account bans, restrictions, or any other consequences resulting from the usage of this code.

## 💬 Support

Need help, suggestions, or want to report a bug? Contact: [@ItsR0Xx](https://t.me/ItsR0Xx) on Telegram.

---
