# Azure App Service Deployment Guide for NBA iDecide Voting System

## Prerequisites
- Microsoft Azure subscription
- Azure App Service plan (B1 minimum recommended)
- Azure Database for PostgreSQL (or use the existing PostgreSQL server)
- Azure Cache for Redis (optional, for production scaling)
- Custom domain configured in Azure
- SSL certificate (Azure App Service provides free managed SSL)

---

## Step 1: Create Azure Resources

### 1.1 Create Resource Group
```bash
az group create --name nba-voting-rg --location eastus
```

### 1.2 Create App Service Plan
```bash
az appservice plan create \
    --name nba-voting-plan \
    --resource-group nba-voting-rg \
    --sku B1 \
    --is-linux
```

### 1.3 Create Web App
```bash
az webapp create \
    --name nba-idecide \
    --resource-group nba-voting-rg \
    --plan nba-voting-plan \
    --runtime "PYTHON|3.11"
```

---

## Step 2: Configure Azure App Settings

Set the following application settings in Azure Portal (Configuration > Application settings):

| Setting Name | Value | Description |
|-------------|-------|-------------|
| `SECRET_KEY` | `[Your Django Secret Key]` | Generate with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | Must be False in production |
| `ALLOWED_HOSTS` | `nba-idecide.azurewebsites.net,your-custom-domain.com` | Your Azure URL and custom domain |
| `BASE_URL` | `https://your-custom-domain.com` | For voting links |
| `DB_NAME` | `[Your PostgreSQL Database Name]` | |
| `DB_USER` | `[Your PostgreSQL User]` | |
| `DB_PASSWORD` | `[Your PostgreSQL Password]` | |
| `DB_HOST` | `[Your PostgreSQL Server].postgres.database.azure.com` | |
| `DB_PORT` | `5432` | |
| `EBULKSMS_USERNAME` | `[Your eBulkSMS Username]` | |
| `EBULKSMS_API_KEY` | `[Your eBulkSMS API Key]` | |
| `WEBSITE_RUN_FROM_PACKAGE` | `1` | Required for Azure deployment |

---

## Step 3: Configure Custom Domain and SSL

### 3.1 Add Custom Domain
1. Go to Azure Portal > Your App Service > Custom domains
2. Click "Add custom domain"
3. Add your domain (e.g., `voting.nbaabuja.org`)
4. Add the provided TXT and CNAME records to your DNS provider
5. Wait for validation

### 3.2 Enable Managed SSL
1. In Custom domains, click "Add TLS/SSL Binding"
2. Select your domain and certificate type (Choose "App Service Managed Certificate" for free SSL)
3. Set TLS type to "HTTPS"

---

## Step 4: Deploy Application

### Option A: Deploy via Azure DevOps/GitHub Actions (Recommended)

Create a GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run migrations
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
      run: |
        python voting_system/manage.py migrate

    - name: Deploy to Azure
      uses: azure/webapps-deploy@v3
      with:
        app-name: 'nba-idecide'
        publish-profile: ${{ secrets.AZURE_PUBLISH_PROFILE }}
        package: .
```

### Option B: Deploy via ZIP file

```bash
# Create deployment package (exclude virtual env and cache)
zip -r deploy.zip . -x "env/*" "*.pyc" "__pycache__/*" ".git/*"

# Deploy to Azure
az webapp deployment source config-zip \
    --resource-group nba-voting-rg \
    --name nba-idecide \
    --src deploy.zip
```

---

## Step 5: Database Migration

After deployment, run migrations via Azure Kudu console or SSH:

1. Go to Azure Portal > Your App Service > SSH
2. Run:
```bash
cd /home/site/wwwroot
python voting_system/manage.py migrate
python voting_system/manage.py createsuperuser
python voting_system/manage.py collectstatic --noinput
```

---

## Step 6: Configure Azure Database for PostgreSQL

### 6.1 Set Firewall Rule
```bash
az postgres server firewall-rule create \
    --resource-group nba-voting-rg \
    --server nba-voting-db \
    --name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0
```

### 6.2 SSL Enforcement
```bash
az postgres server configure-ssl-enforcement \
    --resource-group nba-voting-rg \
    --server nba-voting-db \
    --ssl-enforcement Enabled
```

---

## Step 7: Verify Deployment

1. Access your app at: `https://nba-idecide.azurewebsites.net`
2. Check health endpoint: `https://nba-idecide.azurewebsites.net/health/`
3. Access admin at: `https://nba-idecide.azurewebsites.net/admin/`

---

## Step 8: Send WhatsApp Voting Links

1. Log in to admin panel
2. Go to "Send WhatsApp Message" section
3. Select voters to send voting links
4. Each voter receives a unique link like:
   `https://your-custom-domain.com/vote/[unique-token]/`

---

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with custom domain
- [ ] Set up SSL certificate
- [ ] Enable HTTPS only (redirect HTTP to HTTPS)
- [ ] Set `SECURE_SSL_REDIRECT=True` in Azure settings
- [ ] Configure Azure Redis cache for session/rate limiting
- [ ] Set up monitoring with Azure Application Insights
- [ ] Enable Azure Defender for App Service
- [ ] Configure backup strategy
- [ ] Set up log analytics

---

## Troubleshooting

### Application Doesn't Start
1. Check Application Settings in Azure Portal
2. Review logs in Log Stream: `az webapp log tail --name nba-idecide --resource-group nba-voting-rg`

### Database Connection Error
1. Verify PostgreSQL firewall rules
2. Check `DB_*` application settings
3. Ensure SSL is properly configured

### Static Files Not Loading
1. Run `python manage.py collectstatic`
2. Check `STATIC_ROOT` setting
3. Verify WhiteNoise is in middleware

---

## Support Contact

For issues with the NBA iDecide Voting System, contact the development team.
