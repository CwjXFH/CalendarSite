#!/usr/bin/env bash
rm -rf CalendarSite
git clone https://CwjXFH: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@github.com/CwjXFH/CalendarSite.git
cd CalendarSite
docker compose up --build -d
