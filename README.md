# 🏛️ Civil Service Database Management System

> A comprehensive database application for managing citizen records and government services with modern GUI

[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue.svg)](https://www.mysql.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)

---

## 📋 Overview

The **Civil Service Database Management System** integrates multiple government services into a unified platform:
- **Aadhar** - Citizen identity management
- **PAN** - Tax identification
- **Voter ID** - Electoral registration  
- **SIM Cards** - Telecom service tracking
- **Bank Accounts** - Financial linkage
- **Criminal Records** - Case management

**Tech Stack**: MySQL 8.0 | Python 3.8+ | Tkinter GUI  
**Architecture**: Three-tier (Presentation → Business Logic → Database)

---

## ✨ Key Features

### 👤 For Citizens
- Self-registration with admin approval
- Complete profile dashboard
- Service registration (PAN, Voter ID, SIM, Bank)
- Contact information updates
- Biometric photo capture
- Criminal record verification

### 👨‍💼 For Administrators
- Registration approval/rejection workflow
- Citizen search & management
- Advanced analytics queries
- Database statistics & reporting
- Audit log monitoring
- Photo management system

### 🔒 Security & Validation
- SHA-256 password hashing
- SQL injection protection
- Format validation (PAN, IFSC, EPIC)
- Referential integrity
- Comprehensive audit trails

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
MySQL 8.0+
```

### Installation
```bash
# 1. Clone repository
git clone https://github.com/yourusername/civil-service-db.git
cd civil-service-db

# 2. Install dependencies
pip install mysql-connector-python

# 3. Setup database
mysql -u root -p < setup_complete.sql

# 4. Configure database connection
# Edit DB_CONFIG in civil_service_gui_enhanced_new.py

# 5. Run application
python civil_service_gui_enhanced_new.py
```

### Default Credentials
- **Admin**: `admin` / `admin123`
- **Citizen**: Create new account via registration

---

## 🗄️ Database Architecture

### Schema (12 Tables)
```
aadhar (1:1) ← citizens
  ├── (1:1) → biometrics
  ├── (1:N) → PAN
  ├── (1:N) → votedID
  ├── (1:N) → simCard
  ├── (1:N) → bankAccount
  └── (M:N) → criminalRecord
```

### Advanced SQL Features
- **5 Stored Procedures** - Complex business logic
- **5 User-Defined Functions** - Service counting
- **2 Views** - Simplified queries
- **1 Trigger** - Automatic biometric initialization
- **JOINs** - Multi-table queries
- **Nested Queries** - Aggregation & analytics
- **GROUP BY/HAVING** - Data grouping

### Sample Query (Multi-Bank Accounts)
```sql
SELECT a.UID, a.name, COUNT(ba.AccNo) as accounts,
       GROUP_CONCAT(ba.bankName) as banks
FROM aadhar a
JOIN bankAccount ba ON a.UID = ba.UID
GROUP BY a.UID
HAVING COUNT(ba.AccNo) >= 2;
```

---

## 📊 Technical Specifications

| Component | Details |
|-----------|---------|
| **Database** | MySQL 8.0, InnoDB engine |
| **Backend** | Python 3.8+ |
| **GUI Framework** | Tkinter |
| **Total Code** | ~2,800 lines |
| **Database Objects** | 12 tables, 5 procedures, 5 functions, 2 views |
| **Security** | SHA-256 hashing, parameterized queries |

---

## 📂 Project Structure

```
P2/
├── civil_service_gui_enhanced_new.py  # Main application
├── setup_complete.sql                 # Database setup script
├── requirements.txt                   # Python dependencies
├── PROJECT_REPORT.md                  # Academic report (2-4 pages)
├── README.md                          # This file
└── docs/
    ├── QUICKSTART.md                  # Quick setup guide
    ├── FEATURES.md                    # Feature documentation
    └── INDEX.md                       # Documentation index
```

---

## 🎯 Use Cases

1. **Citizen Registration** - Citizens self-register, admins approve
2. **Service Management** - Link PAN, voter ID, SIM, bank accounts
3. **Identity Verification** - Cross-check services against Aadhar
4. **Analytics** - Find citizens with multiple accounts/voter IDs
5. **Audit Compliance** - Track all system operations
6. **Criminal Records** - Link cases to citizen profiles

---

## 🛡️ Data Validation

| Field | Format | Example |
|-------|--------|---------|
| PAN | 5 letters + 4 digits + 1 letter | `ABCDE1234F` |
| Voter ID (EPIC) | 8 characters | `VOTER001` |
| IFSC Code | 4 letters + 0 + 6 alphanumeric | `ABCD0123456` |
| Aadhar UID | 12 digits | `123456789012` |
| Mobile | 10 digits | `9876543210` |

---

## 📖 Documentation

- **[PROJECT_REPORT.md](PROJECT_REPORT.md)** - Comprehensive academic report (2-4 pages)
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[INDEX.md](INDEX.md)** - Documentation navigation

---

## 🎓 Learning Outcomes

This project demonstrates:
- ✅ **Database Design** - Normalization (1NF, 2NF, 3NF), ER diagrams
- ✅ **SQL Mastery** - DDL, DML, JOINs, nested queries, aggregations
- ✅ **Stored Procedures** - Complex transaction handling
- ✅ **Python Integration** - mysql-connector, GUI development
- ✅ **Security** - Hashing, input validation, SQL injection prevention
- ✅ **Software Engineering** - MVC pattern, code organization

---

## 🚧 Future Enhancements

- [ ] Web interface (Flask/Django)
- [ ] RESTful API
- [ ] Mobile application
- [ ] Multi-factor authentication
- [ ] Real-time notifications
- [ ] Data analytics dashboard
- [ ] Document management

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Database Management Systems Project**  
Course: DBMS | Semester: 5 | Year: 2025

---

## 🙏 Acknowledgments

- MySQL Documentation
- Python Tkinter Resources
- Database Design Best Practices

---

## 📞 Support

For issues or questions:
- Check [QUICKSTART.md](QUICKSTART.md) for common problems
- Review code comments for implementation details
- Consult [PROJECT_REPORT.md](PROJECT_REPORT.md) for technical documentation

---

**⭐ Star this repository if you find it helpful!**
