# LaLouge Project

This project is a comprehensive real estate platform designed to facilitate property management, search, and marketing. It includes features for geolocation-based property mapping, advanced search capabilities, and intelligent pricing suggestions. Built with modern tools and APIs, the platform aims to enhance user experience and provide data-driven solutions for realtors and property seekers.

---

## **Table of Contents**

1. [System Requirements](#system-requirements)  
   - [Ubuntu](#for-ubuntu)  
   - [macOS](#for-macos)  
2. [Database Setup](#database-setup)  
   - [PostgreSQL with PostGIS Extension](#setting-up-postgresql-with-postgis-extension)  
3. [Cloning and Running the Project](#cloning-and-running-the-project)  
4. [Project Features](#project-features)  
5. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)  

---

## **System Requirements**

This project is designed to run on Ubuntu and macOS. Below are the required dependencies.

### **For Ubuntu**

1. **Python**: Version 3.9 or higher.  
   Install via APT:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3 python3-pip python3-venv
   ```

2. **PostgreSQL**: Version 17 or higher with the PostGIS (version 3 or higher) extension.  
   Install via APT:
   ```bash
   sudo apt install postgresql-[version(>=17)] postgresql-[version(>=17)]-postgis-[version(>=3)] postgresql-server-dev-[version(>=17)]
   ```

3. **GDAL and PROJ libraries**: Required for LaLouge to handle spatial data.  
   Install via APT:
   ```bash
   sudo apt install binutils libproj-dev gdal-bin
   ```
4. **Git**: For cloning the repository.  
   Install via APT:
   ```bash
   sudo apt install git
   ```

---

### **For macOS**
    Coming soon

---

## **Database Setup**

This project requires PostgreSQL with the PostGIS extension for spatial data storage.

### **Setting Up PostgreSQL with PostGIS Extension**

1. **Start PostgreSQL Service**:
   ```bash
   sudo service postgresql start  # Ubuntu
   ```

2. **Login to PostgreSQL**:
   ```bash
   sudo -u postgres psql  # Ubuntu
   ```

3. **Create Database and User**:
   ```sql
   CREATE DATABASE db_name;
   CREATE USER db_username WITH PASSWORD 'user_password';
   ALTER ROLE db_username SET client_encoding TO 'utf8';
   ALTER ROLE db_username SET default_transaction_isolation TO 'read committed';
   ALTER ROLE db_username SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE db_name TO db_username;
   ```

4. **Enable PostGIS Extension**:
   Switch to the database:
   ```sql
   \c db_name;
   ```
   Run:
   ```sql
   CREATE EXTENSION postgis;
   ```

---

## **Cloning and Running the Project**

### **1. Clone the Repository**

Use Git to clone the project repository:
```bash
git clone https://github.com/Ramses-Njasap/backend.git
cd backend
```

---

### **2. Create and Activate Virtual Environment**

1. Create a virtual environment:
   ```bash
   python3 -m venv env
   ```
2. Activate the virtual environment:
   ```bash
   source env/bin/activate  # Ubuntu/macOS
   ```

### **3. COPY ENVIRONMENT VARIABLES**

```bash
cp .example.env .env
```

---

### **4. Install Dependencies**

Install required Python packages:
```bash
pip3 install -r requirements.txt
```

---

### **5. Apply Migrations**

Run Django migrations to set up the database:
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

---

### **6. Create Super Admin**

```bash
python3 manage.py createsuperuser
```

---

### **7. Run the Development Server**

Start the development server $PORT=8000:
```bash
daphne LaLouge.asgi:application --port $PORT --bind 0.0.0.0 -v2
```

Celery worker
```bash
celery -A LaLouge worker --loglevel=info
```

Celery beat
```bash
celery -A LaLouge beat --loglevel=info
```

---

### **8. Access the Application**

Visit the following URL in your browser:
```
http://127.0.0.1:8000/admin/
```

Use your superuser credentials to log in to the admin dashboard.

---

## **Project Features**

1. **Boundary Management**:  
   - Add and manage geospatial boundaries using a map in the Django admin panel.
2. **PostGIS Integration**:  
   - Store and query spatial data efficiently using PostgreSQL with PostGIS.
3. **Admin Dashboard**:  
   - Simplified and user-friendly interface to manage spatial data.

---

## **Common Issues and Troubleshooting**

1. **GDAL or PROJ not Found**:  
   Ensure GDAL and PROJ are installed and accessible in your system PATH.

2. **PostGIS Extension Errors**:  
   Verify that the PostGIS extension is enabled for your PostgreSQL database:
   ```sql
   SELECT postgis_full_version();
   ```

3. **Map not Loading in Admin**:  
   - Check network connectivity to OpenStreetMap tile servers.
   - Verify static file configuration and run:
     ```bash
     python3 manage.py collectstatic
     ```

4. **Permission Denied Errors**:  
   Ensure the `db_username` has sufficient privileges:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE db_name TO db_username;
   ```