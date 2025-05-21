# kion-auth

## Status

[![Build](https://github.com/hmrd-forpeople/kion-auth/actions/workflows/build.yml/badge.svg)](https://github.com/hmrd-forpeople/kion-auth/actions/workflows/build.yml)

## Overview

This program is used to screen-scrape AWS CLI credentials from kion and save them to your aws configuration. It assumes you are already connected to zscaler, and will likely fail in strange and unusual ways if you aren't. Ideally, you would run this from a cron/otherwise scheduled job to keep things updated. However, you shouldn't run it every 5 minutes or something, because every time you login to kion, it generates a new set of keys for you, so you'd always be updating (and may accidentally do so while you're in the middle of something important).

As of 20 May 2025, kion tokens expire after 4 hours.

Heavily based on a script written by Steven Angulo (@AX2J-Bixal)

## Support

Currently, this has only been tested on macOS. It _should_ work well on Linux. Windows might need some testing and bugfixes.

## Configuration

kion-auth can be configured either via the command line or from a ini file. An example configuration file (with comments) lives in this directory as example.ini. The default location that this will look for the configuration is `${HOME}/.config/kion-auth.ini`

Command-line arguments take precedence over configuration in the ini file.

```
Usage: kion-auth.py [OPTIONS]

Options:
  --credentials TEXT  Location of AWS Credentials file  [default: /home/user/.aws/credentials]
  --config TEXT       Path of configuration file  [default: /home/user/.config/kion-auth.ini]
  --user TEXT         Username used for logging in to kion
  --password TEXT     Password used for logging in to kion
  --profile TEXT      Name of AWS profile to update
  --log TEXT          Path of log file  [default: /home/user/.log/kion-auth.log]
  --debug             Print extra logging
  --help              Show this message and exit.
  ```

## Installation

See the [install instructions](https://github.com/hmrd-forpeople/kion-auth/wiki/Installation-Instructions)

## Developing

After cloning the repo, first create and activate a virtual environment using python 3.12.x. Next, run `python -m pip install ".[dev]"`. After that, you need to install the chromium shell for playwright by running `python -m playwright install chromium`. Now you're ready to develop on kion-auth!
