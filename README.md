# SmartPOS Retail System 🛒

![Banner](https://img.shields.io/badge/SmartPOS-Retail-blue?style=for-the-badge&logo=django)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-6.0-green?style=for-the-badge&logo=django)

**SmartPOS** is a high-performance, feature-rich Point of Sale (POS) and Inventory Management system built with Django. It is designed to handle modern retail needs, including shift management, advanced inventory tracking (batch/expiry), and seamless checkout experiences.

---

## ✨ Key Features

### 🏪 Point of Sale (POS)
- **AJAX-Powered Cart**: Add/remove products and update quantities without page reloads.
- **Hold & Resume Sale**: Temporarily save a transaction and resume it later.
- **Multi-Payment Support**: Accepts Cash, Card, and Digital Wallets (Bkash/Nagad).
- **Customer Loyalty**: Track customer balances and loyalty points.

### 📦 Inventory & Stock Management
- **Advanced Product Tracking**: Support for Barcodes, Batch Numbers, and Expiry Dates.
- **Stock Movement Logs**: Detailed history of every stock change (Purchases, Sales, Returns).
- **Low Stock Alerts**: Configurable thresholds to notify when items are running low.
- **Category Management**: Organize products for better filtering and reporting.

### 👥 User & Shift Management
- **Role-Based Access**: Specialized views for Admins, Managers, and Cashiers.
- **Shift Tracking**: Track opening/closing balances and cashier performance per shift.
- **User Profiles**: Detailed profiles for all employees.

### 💰 Financials & Reporting
- **Expense Tracking**: Log and categorize shop expenses.
- **Sales Returns**: Process returns with automatic stock restoration and refunds.
- **Tax & Currency**: Globally configurable tax percentages and currency symbols.

---

## 🛠️ Tech Stack

- **Backend**: [Django](https://www.djangoproject.com/)
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6), AJAX (jQuery/Fetch)
- **Database**: SQLite (Default)
- **Security**: Django Auth with custom Role-based Middleware

---

## 🚀 Installation & Setup

### 1. Clone & Navigate
```bash
git clone https://github.com/your-repo/smartpos.git
cd smartpos/pos_project
```

### 2. Virtual Environment
```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
```

### 3. Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Admin
```bash
python manage.py createsuperuser
```

### 6. Run Server
```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

---

## 📁 System Architecture

```text
pos_project/
├── pos_app/            # Main Logic & Models
│   ├── models.py       # Inventory, Sales, Shifts, etc.
│   ├── views.py        # POS & Dashboard Logic
│   └── signals.py      # Automated Stock Updates
├── pos_project/        # Core Configuration
├── templates/          # Modern UI Layouts
├── static/             # CSS & Interactive JS
└── media/              # Product & Setting Images
```

---

## 🛡️ License
Proprietary software. All rights reserved.

---

Developed for high-efficiency retail environments. 🚀
