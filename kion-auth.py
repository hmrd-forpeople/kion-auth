#! /usr/bin/env python3
# This program is used to screen-scrape AWS CLI credentials from
# kion and save them to your aws configuration. It assumes you are
# already connected to zscaler, and will likely fail in strange and
# unusual ways if you aren't. Ideally, you would run this from a
# cron/otherwise scheduled job to keep things updated. However,
# you shouldn't run it every 5 minutes or something, because every
# time you login to kion, it generates a new set of keys for you,
# so you'd always be updating (and may accidentally do so while
# you're in the middle of something important).
#
# As of 20 May 2025, kion tokens expire after 4 hours.
#
# Heavily based on a script written by Steven Angulo (@AX2J-Bixal)
import logging
import logging.handlers
import os
import re
import subprocess  # nosec: B404 this is all trusted inputs
import sys
import time
from configparser import ConfigParser

import click
from click.core import ParameterSource as Source
from playwright.sync_api import sync_playwright


def die(msg):
    """Print a message to stderr, and exit with a failure."""
    logging.fatal(msg)
    print(msg, file=sys.stderr)
    sys.exit(1)


def get_auth_1password(cfg) -> tuple[str, str]:
    """Get authentication configuration from 1password"""
    op_vault = cfg.get("vault")
    op_item = cfg.get("item")
    op_userkey = cfg.get("userkey", "username")
    op_passkey = cfg.get("passkey", "password")
    op_binary = cfg.get("op_binary", "/opt/homebrew/bin/op")

    username = (
        subprocess.check_output(
            [op_binary, "read", f"op://{op_vault}/{op_item}/{op_userkey}"]
        )  # nosec
        .decode("utf-8")
        .strip()
    )
    password = (
        subprocess.check_output(
            [op_binary, "read", f"op://{op_vault}/{op_item}/{op_passkey}"]
        )  # nosec
        .decode("utf-8")
        .strip()
    )

    return username, password


def update_aws_credentials(creds_file_path, profile_name, access_key, secret_key, session_token):
    """Given the new access key, secret key, and session token, save
    them for the named profile in the file indicated.
    """
    logging.info(f"Updating credentials in {creds_file_path}")
    # Initialize ConfigParser and read the credentials file
    config = ConfigParser()
    config.read(creds_file_path)

    # Ensure the profile exists in the credentials file, create it if missing
    if profile_name not in config.sections():
        logging.debug(f"Adding section {profile_name}")
        config.add_section(profile_name)

    if (
        config[profile_name].get("aws_access_key_id") == access_key
        and config[profile_name].get("aws_secret_access_key") == secret_key
        and config[profile_name].get("aws_session_token") == session_token
    ):
        logging.info("Access key unchanged, not updating")
        return

    # Update the profile with new credentials
    config[profile_name]["aws_access_key_id"] = access_key
    config[profile_name]["aws_secret_access_key"] = secret_key
    config[profile_name]["aws_session_token"] = session_token

    # Write the updated configuration back to the file
    with open(creds_file_path, "w") as creds_file:
        config.write(creds_file)

    logging.info(f"Credentials for profile [{profile_name}] updated successfully.")


def get_new_aws_credentials(user: str, password: str) -> tuple[str, str, str]:
    """Retrieve new AWS CLI credentials from kion by screen-scraping."""
    logging.info("Scraping AWS credentials from kion")
    with sync_playwright() as p:

        # Set headless=True for no UI
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # TODO: we could paramaterize this.
        # Navigate to cloudtamer
        page.goto("https://cloudtamer.cms.gov/login")

        # Authenticate
        page.fill("input[formcontrolname='username']", user)
        page.fill("input[formcontrolname='password']", password)
        log_in_button_locator = page.locator('button:text("Log")')
        log_in_button_locator.click()

        # Give the site time to load
        time.sleep(3)

        # Use page.locator() to click the "Ok" button based on its text content
        ok_button_locator = page.locator('button:text("Ok")')
        ok_button_locator.click()

        # Load the new short-term keys by opening that page item.
        new_content_selector = "div.quick-cloud-access-item.card.card-body.pg-p-2.pg-mb-1"
        page.click(new_content_selector)

        # Sleep to let the page load the keys
        time.sleep(3)

        # Regex pattern to match the AWS CLI credential keys
        aws_cred_pattern = r"aws_access_key_id\s*=\s*([A-Za-z0-9+/=]+)\s*aws_secret_access_key\s*=\s*([A-Za-z0-9+/=]+)\s*aws_session_token\s*=\s*([A-Za-z0-9+/=]+)"  # noqa: B950

        # Find all matches in the page body text
        page_text = page.inner_text("body")
        matches = re.findall(aws_cred_pattern, page_text)

        if matches:
            access_key, secret_key, session_token = matches[0]
            # Print the extracted values (just for confirmation)
            logging.debug(f"Access Key: {access_key}")
            logging.debug(f"Secret Key: {secret_key}")
            logging.debug(f"Session Token: {session_token}")
            return access_key, secret_key, session_token
        else:
            die("No AWS credentials found on the page.")


@click.command()
@click.option(
    "--credentials",
    help="Location of AWS Credentials file",
    default=os.path.join(os.getenv("HOME"), ".aws", "credentials"),
    show_default=True,
)
@click.option(
    "--config",
    help="Path of configuration file",
    default=os.path.join(os.getenv("HOME"), ".config", "kion-auth.ini"),
    show_default=True,
)
@click.option("--user", help="Username used for logging in to kion")
@click.option("--password", help="Password used for logging in to kion")
@click.option("--profile", help="Name of AWS profile to update")
@click.option(
    "--log",
    help="Path of log file",
    default=os.path.join(os.getenv("HOME"), ".log", "kion-auth.log"),
    show_default=True,
)
@click.option("--debug", is_flag=True, help="Print extra logging")
@click.pass_context
def main(ctx, credentials, config, user, password, profile, log, debug):
    # Read configuration from the file if it exists, otherwise start
    # with an empty configuration and hope the user used the CLI args
    # Configuration prefers the CLI arguments if given, otherwise it
    # takes information from the config file.
    if os.path.exists(config):
        c = ConfigParser()
        c.read(config)
        cfg = c["kion_auth"]
    else:
        cfg = {}

    # We only want to override the log destination from the config
    # file if the user explicitly passed it in from the CLI.
    if ctx.get_parameter_source("log") == Source.DEFAULT and cfg.get("log"):
        log = cfg.get("log")

    if log == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.handlers.RotatingFileHandler(log, backupCount=1, maxBytes=1024 * 1024)

    log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        level=log_level,
        handlers=[handler],
    )

    auth_source = cfg.get("auth_source")
    if auth_source == "1password":
        source_user, source_password = get_auth_1password(cfg)
    else:
        source_user = cfg.get("user")
        source_password = cfg.get("password")

    if not user:
        user = source_user
    if not password:
        password = source_password

    if not profile:
        profile = cfg.get("profile")

    # Just like the log destination file, we only want to override
    # what came in from the CLI args if what came in was the default
    if ctx.get_parameter_source("credentials") == Source.DEFAULT and cfg.get("credentials"):
        credentials = cfg.get("credentials")

    if not all([user, password, profile, credentials]):
        die(
            "Missing one configuration. Ensure configurtion file exists or all arguments are passed"
        )

    logging.debug(f"User: {user}")
    logging.debug(f"Profile: {profile}")
    logging.debug(f"Credentials File: {credentials}")

    access_key, secret_key, session_token = get_new_aws_credentials(user, password)
    update_aws_credentials(credentials, profile, access_key, secret_key, session_token)


if __name__ == "__main__":
    main()
