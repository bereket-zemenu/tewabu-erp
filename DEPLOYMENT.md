# 🚀 How to Deploy Tewabu ERP for Free (24/7 Hosting)

You can host your Telegram bot online 24/7 completely free without keeping your computer running. Here are the top 3 recommended free methods:

---

## Method 1: Koyeb (Recommended — Easiest & 100% Free 24/7)

Koyeb offers a **Free Eco tier** that does **not sleep** and requires no credit card.

### Steps:
1. Push your code to a private or public repository on [GitHub](https://github.com).
2. Go to [koyeb.com](https://www.koyeb.com) and create a free account.
3. Click **Create App** and select **GitHub**.
4. Choose your `tewabu-erp` repository.
5. In **Builder**, select **Dockerfile** (it will automatically use the `Dockerfile` in the project).
6. Under **Environment Variables**, add:
   - `BOT_TOKEN` = `your_bot_token_from_botfather`
   - `ACCESS_PASSWORD` = `122337`
   - `DEFAULT_CURRENCY` = `ETB`
   - `DEFAULT_PROFIT_MARGIN` = `0.25`
   - `DEFAULT_LANGUAGE` = `am`
7. Click **Deploy**. Within 2 minutes, your bot will be running online 24/7!

---

## Method 2: Render.com (Free Tier)

Render allows free hosting directly connected to your GitHub repository.

### Steps:
1. Push your code to [GitHub](https://github.com).
2. Sign up at [render.com](https://render.com).
3. Click **New +** → **Background Worker** (or **Web Service**).
4. Connect your GitHub repository.
5. Settings:
   - **Environment**: `Python 3` (or `Docker`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
6. Under **Environment Variables**, add:
   - `BOT_TOKEN`
   - `ACCESS_PASSWORD`
7. Click **Create Service**.

---

## Method 3: Oracle Cloud "Always Free" VPS (Best for Persistent Database)

Oracle Cloud gives you **2 free Linux Virtual Machines forever** with dedicated storage. This is ideal if you want your SQLite database records preserved forever without any file system resets.

### Steps:
1. Sign up for [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
2. Create an **Always Free Compute Instance** (Ubuntu 24.04).
3. Connect via SSH:
   ```bash
   ssh -i your_key.pem ubuntu@your_server_ip
   ```
4. Install Python and Git:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git
   ```
5. Clone your bot and set up the virtual environment:
   ```bash
   git clone https://github.com/yourusername/tewabu-erp.git
   cd tewabu-erp
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   nano .env  # paste your BOT_TOKEN and save
   ```
6. Set up Systemd service to auto-restart on boot:
   ```bash
   sudo nano /etc/systemd/system/tewabu.service
   ```
   Paste:
   ```ini
   [Unit]
   Description=Tewabu ERP Telegram Bot
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/tewabu-erp
   ExecStart=/home/ubuntu/tewabu-erp/.venv/bin/python bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```
7. Start and enable the bot service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tewabu
   sudo systemctl start tewabu
   ```
   Check status:
   ```bash
   sudo systemctl status tewabu
   ```

Your bot will now run permanently 24/7, even through server reboots!
