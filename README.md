# MensemDiscord

Discord bot for Mensem community with verification, staff recruitment, tickets, events, logs, banners, welcome cards, and a small status web app.

## Run locally

```bash
pip install -r requirements.txt
python main.py
```

## Required environment

Create a `.env` file from `.env.example` and fill in:

- `TOKEN`
- `GUILD_ID`
- Discord role and channel IDs for the active modules
- `PORT` only if your host requires it

## Render

The repository includes:

- `render.yaml`
- `Procfile`
- `/health` endpoint in the web app

Render can start the project with:

```bash
python main.py
```

## Notes

- Do not commit `.env`, database files, or generated banner images.
- `banner` and `welcome` use local background assets if you do not override their paths in `.env`.
- The bot loads modules from `main.py` through `loader.py`.

