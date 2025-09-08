# Supply Chain Automation System

A comprehensive, modular supply chain automation platform with specialized bots for inventory management, supplier communication, auto-reordering, and demand forecasting. Features seamless Zapier integration and Stripe subscription management.

## 🚀 Features

- **Inventory Management Bot**: Real-time stock monitoring, stockout/overstock alerts, automated threshold management
- **Supplier Management Bot**: Streamlined supplier communication, request management, performance tracking
- **Auto-Reorder Bot**: Smart reordering with configurable triggers and demand-based automation
- **Demand Forecasting Bot**: AI-powered demand prediction and inventory optimization
- **Zapier Integration**: Connect to 5000+ apps with webhook-based triggers
- **Stripe Integration**: Subscription management and billing automation
- **Web Dashboard**: Comprehensive control panel with real-time analytics

## 🏗️ Architecture

Built with modern, scalable technologies:
- **Backend**: Flask (Python)
- **Frontend**: HTML5, Tailwind CSS, Chart.js
- **Database**: SQLite (easily upgradeable)
- **Integration**: REST API with webhook support

## 📦 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/supply-chain-automation.git
cd supply-chain-automation
```

2. **Set up virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python src/main.py
```

5. **Access the dashboard**
Open your browser and go to `http://localhost:5001`

## 🔧 Configuration

Create a `.env` file in the root directory:

```env
FLASK_ENV=development
DATABASE_URL=sqlite:///src/database/app.db
STRIPE_API_KEY=your_stripe_api_key_here
ZAPIER_WEBHOOK_SECRET=your_webhook_secret_here
```

## 📊 API Endpoints

### Inventory Management
- `GET /api/inventory/products` - List all products
- `POST /api/inventory/products` - Add new product
- `GET /api/inventory/alerts` - Get stock alerts
- `POST /api/inventory/update` - Update stock levels

### Supplier Management
- `GET /api/suppliers` - List suppliers
- `POST /api/suppliers/requests` - Create supplier request
- `GET /api/suppliers/performance` - Get supplier metrics

### Auto-Reorder
- `POST /api/reorder/trigger` - Trigger manual reorder
- `GET /api/reorder/rules` - Get reorder rules
- `POST /api/reorder/rules` - Create reorder rule

### Webhooks (Zapier Integration)
- `POST /api/webhooks/subscribe` - Subscribe to events
- `GET /api/webhooks/events` - Get recent events
- `GET /api/zapier/triggers` - List available triggers

### Subscriptions (Stripe Integration)
- `POST /api/subscription/create` - Create subscription
- `GET /api/subscription/status` - Check subscription status

## 🔗 Zapier Integration

Connect your supply chain automation to 5000+ apps:

1. Create a new Zap in Zapier
2. Choose "Webhooks by Zapier" as trigger
3. Select "Catch Hook"
4. Copy the webhook URL
5. Subscribe to events using our API:

```bash
curl -X POST http://your-domain.com/api/webhooks/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_event": "inventory.stockout",
    "webhook_url": "your_zapier_webhook_url"
  }'
```

### Available Triggers
- `inventory.stockout` - When product goes out of stock
- `inventory.overstock` - When product exceeds maximum threshold
- `inventory.reorder` - When auto-reorder is triggered
- `supplier.request_created` - When new supplier request is made
- `forecasting.demand_spike` - When demand spike is detected

## 💳 Stripe Integration

Enable subscription management:

1. Get your Stripe API keys from the Stripe Dashboard
2. Add them to your `.env` file
3. Use the subscription endpoints to manage customer billing

## 🚀 Deployment

### Production Deployment

1. **Install Gunicorn**
```bash
pip install gunicorn
```

2. **Run with Gunicorn**
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 "src.main:app"
```

3. **Set up Nginx reverse proxy** (optional but recommended)

### Docker Deployment

```bash
docker build -t supply-chain-automation .
docker run -p 5001:5001 supply-chain-automation
```

## 📁 Project Structure

```
supply_chain_orchestrator/
├── src/
│   ├── models/              # Database models
│   ├── routes/              # API route handlers
│   │   ├── inventory.py     # Inventory management
│   │   ├── supplier.py      # Supplier management
│   │   ├── reorder.py       # Auto-reorder logic
│   │   ├── forecasting.py   # Demand forecasting
│   │   ├── webhooks.py      # Zapier integration
│   │   └── subscription.py  # Stripe integration
│   ├── static/              # Frontend dashboard
│   │   └── index.html       # Main dashboard
│   ├── main.py              # Flask application
│   └── database/
│       └── app.db           # SQLite database
├── venv/                    # Virtual environment
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in this repository
- Check the [documentation](docs/)
- Contact: support@yourcompany.com

## 🔄 Changelog

### v1.0.0
- Initial release
- Complete supply chain automation system
- Zapier and Stripe integrations
- Web dashboard with real-time analytics
- Multi-bot architecture with specialized functions

---

**Built with ❤️ for supply chain professionals**

