# kion-auth

## Status

[![Build](https://github.com/hmrd-forpeople/kion-auth/actions/workflows/build.yml/badge.svg)](https://github.com/hmrd-forpeople/kion-auth/actions/workflows/build.yml)

## Overview

This program is used to screen-scrape AWS CLI credentials from kion and save them to your aws configuration. It assumes you are already connected to zscaler, and will likely fail in strange and unusual ways if you aren't. Ideally, you would run this from a cron/otherwise scheduled job to keep things updated. However, you shouldn't run it every 5 minutes or something, because every time you login to kion, it generates a new set of keys for you, so you'd always be updating (and may accidentally do so while you're in the middle of something important).

As of 20 May 2025, kion tokens expire after 4 hours.

Heavily based on a script written by Steven Angulo (@AX2J-Bixal)

## Support

Currently, this has only been tested on macOS. It _should_ work well on Linux. Windows might need some testing and bugfixes.

## Installation

See the [install instructions](https://github.com/hmrd-forpeople/kion-auth/wiki/Installation-Instructions)

## Configuration

See the [configuration instructions](https://github.com/hmrd-forpeople/kion-auth/wiki/Configuration)
