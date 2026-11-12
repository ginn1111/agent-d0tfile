SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help
-include .env
export

.PHONY: help cf-tunnel

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make cf-tunnel   # run cloudflared tunnel container (CF_TOKEN from .env)'

cf-tunnel:
	@docker run --network host -d --name cf_hermes_profiles cloudflare/cloudflared:latest tunnel --no-autoupdate run --token ${CF_TOKEN}
