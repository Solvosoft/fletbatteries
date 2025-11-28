# FletBatteries

FletBatteries is a set of framework-like tools designed to simplify 
the development of applications with Flet. This project provides a 
user-friendly and highly customizable environment, ideal for developers 
looking to create applications efficiently and quickly

---

## 📋 Table of Contents

1. [Features](#-features)
2. [Requirements](#-requirements)
3. [Installation](#-installation)
4. [Usage](#-usage)
5. [Project Structure](#-project-structure)
6. [Useful Links](#-useful-links)

---

## 🚀 Features

* View routing system.
* Modular and extensible architecture.
* Modern and responsive UI with Flet.

---

## 🛠️ Requirements

* Python 3.11+
* pip

---

## ⚙️ Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/Solvosoft/fletbatteries.git
   cd fletbatteries
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   make requirements
   ```
   
4. Database init:
   ```bash
   make init_db
   ```
   
5. Run API
   ```bash
   uvicorn scripts.api:app --reload --app-dir src
   ```

Si no tiene una base de datos

---

## 📦 Usage

Run the Flet application:

```bash
make run
```

This will open a window where you can:

* Start the project
* Create and test views

---

## 📂 Project Structure

```text
template/
├── .venv/                   # Virtual environment
├── src/                     # Main source code
│   ├── assets/              # Static assets
│   │   ├── image/           # Images used in the app
│   │   ├── fonts/           # Fonts used in the app
│   │   └── fontawesome/     # Icons used in the app
│   ├── components/          # Reusable components
│   │   ├── layout/          # General layout and design
│   │   └── share/           # Shared components
│   ├── controls/            # Control logic and validation
│   │   ├── handler/         # Logic for view handling
│   │   └── router/          # Custom routing logic
│   ├── data/                # Data handling
│   │   ├── models/          # Data models and schemas
│   │   └── manager/         # CRUD operations
│   ├── views/               # Visual logic and UI views
│   │   └── main.py          # App entry point
│   └── scripts/             # App scripts
├── .gitignore               # Git ignore rules
├── Makefile                 # Automation tasks
├── README.md                # Project documentation
└── requirements.txt         # Project dependencies
```

---

## 🔗 Useful Links

* **Flet (documentation)**: [https://flet.dev/docs/](https://flet.dev/docs/)
