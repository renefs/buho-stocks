# Buho Stocks

<p align="center"><img src="logo.png" alt="Buho-Stocks logo" height="200"></p>

<p align="center">Application to manage and track a stocks portfolio with dividends and return for a <a href="https://en.wikipedia.org/wiki/Buy_and_hold" title="Wikipedia">Buy & Hold investment</a> investment strategy.</p>

<p align="center">
<img src="https://github.com/bocabitlabs/buho-stocks/actions/workflows/django.yml/badge.svg" href="https://github.com/bocabitlabs/buho-stocks/actions/workflows/django.yml" alt="Django CI"/> <img src="https://github.com/bocabitlabs/buho-stocks/actions/workflows/react.yml/badge.svg" href="https://github.com/bocabitlabs/buho-stocks/actions/workflows/react.yml" alt="React CI"/> <a href="https://codecov.io/github/bocabitlabs/buho-stocks" > 
 <img src="https://codecov.io/github/bocabitlabs/buho-stocks/graph/badge.svg?token=GeXfRGSLzP"/> 
 </a>
</p>
<p align="center">
  • <a href="#features">Features</a> •
  <a href="#install">Install</a> •
  <a href="#development">Development</a> •
  <a href="#links">Links</a> •
  <a href="#attributions">Attributions</a> •
  <a href="#screenshots">Screenshots</a> •
</p>

## 🚀 Motivation

Using a spreadsheet to manage a portfolio can become a complicated and tedious task, as well as calculating investment returns. That's why I decided to create this application, to simplify these periodic and monotonous tasks of portfolio management.

## 🎁 Features

| Feature                                                                    | Implemented |
| -------------------------------------------------------------------------- | ----------- |
| Unlimited portfolios                                                       | ✅          |
| Unlimited companies per portfolio                                          | ✅          |
| Support for stock transactions, dividends and rights                       | ✅          |
| Unlimited sectors and subsectors                                           | ✅          |
| Import CSV files from Interactive Brokers                                  | ✅          |
| Fetch stock prices and exchange rates from a external source in real time. | ✅          |
| Multiple charts: dividends, returns, sectors, currencies...                | ✅          |
| Support for multiple languages                                             | ✅          |

## 📚 Documentation

Documentation is available on [Github Pages](https://bocabitlabs.github.io/buho-stocks/).

## ⚛️ Technologies used

### Frontend

- React 18
- TypeScript
- Mantine UI 7
- Vite
- TanStack Query

### Backend

- Python 3.10+
- Django 5
- Django REST Framework
- Celery (background tasks)
- Channels (WebSockets)

### Infrastructure

- Docker & Docker Compose
- Redis (message broker & cache)
- MariaDB (production database)
- Nginx (reverse proxy)
- uv (Python dependency management)

## 📋 Requirements

For local development:

- Python 3.11
- Node.js 20
- Redis
- uv

## 🫂 How to contribute

If you want to participate on the project, please take a look at
the [CONTRIBUTING file](https://github.com/bocabitlabs/buho-stocks/blob/main/.github/CONTRIBUTING.md) as it includes information about the branching and commit guideliness.

You can find information about how to configure the development environment on the [DEVELOPMENT docs](https://bocabitlabs.github.io/buho-stocks/)

## 📘 Usage and deployment guides

Usage and deployment guides are available on the [Documentation](https://bocabitlabs.github.io/buho-stocks/)

## 🙏 Attributions

- Illustrations: https://undraw.co/search
- Logo by [lavarmsg](https://www.vecteezy.com/members/lavarmsg)

## 📝 License

[GPL 3](LICENSE)

All 3rd party logos are property of their owners.

## 🍺 Donate

<a href="https://paypal.me/renefs/"><img src="donate-blue.svg" height="40"></a>

If you like this project — or just feeling generous, consider buying me a beer. Cheers! 🍻

## 🖼️ Screenshots

See the [documentation](https://bocabitlabs.github.io/buho-stocks/) for screenshots and usage examples.
