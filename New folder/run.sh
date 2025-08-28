#!/bin/bash
# simple run script for local environment
if [ ! -f ".env" ]; then
  echo "Please copy .env.example to .env and fill TG_TOKEN and TG_CHAT_ID"
  exit 1
fi
export $(grep -v '^#' .env | xargs)
python init_db.py
python main.py
