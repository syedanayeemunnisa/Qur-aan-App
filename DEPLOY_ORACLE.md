# 🚀 Deploy to Oracle Cloud Free Tier (Always Free)

Oracle Cloud offers **always-free** ARM instances with 24GB RAM — perfect for running EasyOCR.

## Step 1: Create Oracle Cloud Account

1. Go to https://cloud.oracle.com/free
2. Sign up for Free Tier (credit card required for verification, won't be charged)
3. Choose **Always Free** resources

## Step 2: Create VM Instance

1. Go to **Compute > Instances > Create Instance**
2. Choose these settings:
   - **Name**: `qur-aan-app`
   - **Image**: Ubuntu 22.04 or 24.04 (ARM)
   - **Shape**: **VM.Standard.A1.Flex** (ARM, always free)
   - **OCPU**: 4 (max free)
   - **RAM**: 24 GB (max free)
   - **Boot Volume**: 50 GB

3. Create SSH key pair:
   - Click **Generate SSH Keys**
   - Download both public and private keys
   - Save them securely

4. Click **Create** and wait for instance to be running

## Step 3: Connect to Your VM

```bash
# SSH into your instance
ssh -i /path/to/your-key.pem ubuntu@<YOUR_PUBLIC_IP>
```

Find your public IP in the Oracle Cloud console under your instance details.

## Step 4: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies for OpenCV and Tesseract
sudo apt install -y libgl1-mesa-glx libglib2.0-0 tesseract-ocr tesseract-ocr-ara

# Install Docker (optional, but easier)
sudo apt install -y docker.io
sudo usermod -aG docker $USER
# Log out and log back in for docker group to take effect
```

## Step 5: Deploy the App

### Option A: Using Docker (Recommended)

```bash
# Clone your repo
git clone https://github.com/syedanayeemunnisa/Qur-aan-App.git
cd Qur-aan-App

# Build and run with Docker
docker build -t qur-aan-app -f backend/Dockerfile backend/
docker run -d -p 80:10000 --name qur-aan-app --restart unless-stopped qur-aan-app
```

### Option B: Manual Setup

```bash
# Clone your repo
git clone https://github.com/syedanayeemunnisa/Qur-aan-App.git
cd Qur-aan-App/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (CPU-only PyTorch)
pip install --upgrade pip
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Run the server
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 80 &
```

## Step 6: Open Firewall Ports

In Oracle Cloud Console:
1. Go to your VCN > Security Lists
2. Add Ingress Rule:
   - **Source CIDR**: 0.0.0.0/0
   - **Destination Port**: 80 (or 443 for HTTPS)
   - **Protocol**: TCP

## Step 7: Update Web App API URL

After deployment, update the web app to point to your Oracle Cloud IP:

1. Edit `backend/templates/index.html`
2. Find this line:
   ```javascript
   const API = window.location.hostname === 'localhost' 
     ? '/api/v1' 
     : 'https://qur-aan-app-backend.onrender.com/api/v1';
   ```
3. Replace with:
   ```javascript
   const API = window.location.hostname === 'localhost' 
     ? '/api/v1' 
     : 'http://YOUR_ORACLE_IP/api/v1';
   ```

4. Commit and push:
   ```bash
   git add backend/templates/index.html
   git commit -m "Update API URL for Oracle Cloud"
   git push
   ```

## Step 8: Access Your App

- **Web App**: https://qur-aan-app.pages.dev (Cloudflare Pages)
- **Backend API**: http://YOUR_ORACLE_IP/api/v1/health

## Optional: Add HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot

# Get SSL certificate (requires domain pointing to your IP)
sudo certbot certonly --standalone -d your-domain.com

# Update nginx or use with your app
```

## Troubleshooting

### Check if server is running
```bash
curl http://localhost/api/v1/health
```

### View logs
```bash
docker logs qur-aan-app
# or
journalctl -u your-service-name
```

### Restart server
```bash
docker restart qur-aan-app
# or
sudo systemctl restart your-service-name
```

## Cost

- **Always Free**: $0/month
- **Includes**: 4 OCPU, 24GB RAM, 200GB storage
- **No time limit**: Runs forever at no cost
