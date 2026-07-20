SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

GLOBAL_HERMES_HOME := $(shell printf '%s\n' "$$HOME" | sed -E 's#^(.*)/\.hermes/profiles/[^/]+/home.*#\1/.hermes#; t; s#$$#/.hermes#')
HERMES_PROFILES_DIR ?= $(GLOBAL_HERMES_HOME)/profiles
HERMES_PROFILE_CACHE := .make/hermes-profiles.mk
PROFILE ?=
HEALTH_PATH ?= /v1/models
include .env
export

.PHONY: help hermes-profiles-config hermes-health hermes-health-auth hermes-health-noauth hermes-health-debug

define curl_status
code="$$(curl -sS -o /dev/null -w '%{http_code}' $(1) '$(PROFILE_URL)$(HEALTH_PATH)' || printf '000')"; \
if [ "$$code" = "200" ]; then \
  printf '%s\n' "healthy PROFILE=$(PROFILE) PATH=$(HEALTH_PATH) HTTP=$$code"; \
else \
  printf '%s\n' "unhealthy PROFILE=$(PROFILE) PATH=$(HEALTH_PATH) HTTP=$$code"; \
  exit 1; \
fi
endef

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make hermes-profiles-config              # build profile map from ~/.hermes/profiles/*/.env' \
	  '  make hermes-health PROFILE=<name>        # auth-route status: healthy/unhealthy' \
	  '  make hermes-health-auth PROFILE=<name>   # auth-route status with Bearer token from profile env' \
	  '  make hermes-health-noauth PROFILE=<name> # auth-route status without Authorization header' \
	  '  make hermes-health-debug PROFILE=<name>  # print resolved URL/token presence, not token' \
	  '' \
	  'Vars:' \
	  '  PROFILE=<hermes-profile>' \
	  '  HEALTH_PATH=/v1/models'

hermes-profiles-config:
	@mkdir -p $(dir $(HERMES_PROFILE_CACHE))
	@python3 scripts/hermes_profile_map.py "$(HERMES_PROFILES_DIR)" > "$(HERMES_PROFILE_CACHE)"
	@printf 'Wrote %s\n' '$(HERMES_PROFILE_CACHE)'

-include $(HERMES_PROFILE_CACHE)

ifeq ($(strip $(PROFILE)),)
PROFILE_KEY :=
PROFILE_URL :=
PROFILE_TOKEN :=
else
PROFILE_KEY := $(shell printf '%s' '$(PROFILE)' | sed 's/[^A-Za-z0-9_]/_/g')
PROFILE_URL := $(HERMES_PROFILE_$(PROFILE_KEY)_URL)
PROFILE_TOKEN := $(HERMES_PROFILE_$(PROFILE_KEY)_TOKEN)
endif

hermes-health: hermes-profiles-config
	@profile='$(PROFILE)'; \
	if [ -z "$$profile" ]; then \
	  printf 'Enter Hermes profile [%s]: ' "$(firstword $(HERMES_PROFILE_NAMES))"; \
	  read -r profile; \
	  profile="$${profile:-$(firstword $(HERMES_PROFILE_NAMES))}"; \
	fi; \
	if [ -z "$(HERMES_PROFILE_$(PROFILE_KEY)_URL)" ] && [ "$$profile" = "$(PROFILE)" ]; then :; fi; \
	$(MAKE) --no-print-directory hermes-health-inner PROFILE="$$profile" HEALTH_PATH='$(HEALTH_PATH)'

hermes-health-auth: hermes-profiles-config
	@profile='$(PROFILE)'; \
	if [ -z "$$profile" ]; then \
	  printf 'Enter Hermes profile [%s]: ' "$(firstword $(HERMES_PROFILE_NAMES))"; \
	  read -r profile; \
	  profile="$${profile:-$(firstword $(HERMES_PROFILE_NAMES))}"; \
	fi; \
	$(MAKE) --no-print-directory hermes-health-auth-inner PROFILE="$$profile" HEALTH_PATH='$(HEALTH_PATH)'

hermes-health-noauth: hermes-profiles-config
	@profile='$(PROFILE)'; \
	if [ -z "$$profile" ]; then \
	  printf 'Enter Hermes profile [%s]: ' "$(firstword $(HERMES_PROFILE_NAMES))"; \
	  read -r profile; \
	  profile="$${profile:-$(firstword $(HERMES_PROFILE_NAMES))}"; \
	fi; \
	$(MAKE) --no-print-directory hermes-health-noauth-inner PROFILE="$$profile" HEALTH_PATH='$(HEALTH_PATH)'

hermes-health-debug: hermes-profiles-config
	@profile='$(PROFILE)'; \
	if [ -z "$$profile" ]; then \
	  printf 'Enter Hermes profile [%s]: ' "$(firstword $(HERMES_PROFILE_NAMES))"; \
	  read -r profile; \
	  profile="$${profile:-$(firstword $(HERMES_PROFILE_NAMES))}"; \
	fi; \
	$(MAKE) --no-print-directory hermes-health-debug-inner PROFILE="$$profile" HEALTH_PATH='$(HEALTH_PATH)'

hermes-health-inner: hermes-profiles-config
	@if [ -z "$(PROFILE_URL)" ]; then \
	  echo "Unknown or disabled profile: $(PROFILE)"; \
	  echo 'Run: make hermes-profiles-config'; \
	  echo "Known profiles: $(HERMES_PROFILE_NAMES)"; \
	  exit 1; \
	fi
	@if [ -n "$(PROFILE_TOKEN)" ]; then \
	  $(MAKE) --no-print-directory hermes-health-auth-inner PROFILE='$(PROFILE)' HEALTH_PATH='$(HEALTH_PATH)'; \
	else \
	  $(MAKE) --no-print-directory hermes-health-noauth-inner PROFILE='$(PROFILE)' HEALTH_PATH='$(HEALTH_PATH)'; \
	fi

hermes-health-auth-inner: hermes-profiles-config
	@if [ -z "$(PROFILE_URL)" ]; then \
	  echo "Unknown or disabled profile: $(PROFILE)"; \
	  echo "Known profiles: $(HERMES_PROFILE_NAMES)"; \
	  exit 1; \
	fi
	@if [ -z "$(PROFILE_TOKEN)" ]; then \
	  echo "Profile $(PROFILE) has no API_SERVER_KEY"; exit 1; \
	fi
	@$(call curl_status,-H "Authorization: Bearer $(PROFILE_TOKEN)")

hermes-health-noauth-inner: hermes-profiles-config
	@if [ -z "$(PROFILE_URL)" ]; then \
	  echo "Unknown or disabled profile: $(PROFILE)"; \
	  echo "Known profiles: $(HERMES_PROFILE_NAMES)"; \
	  exit 1; \
	fi
	@$(call curl_status,)

hermes-health-debug-inner: hermes-profiles-config
	@if [ -z "$(PROFILE_URL)" ]; then \
	  echo "Unknown or disabled profile: $(PROFILE)"; \
	  echo "Known profiles: $(HERMES_PROFILE_NAMES)"; \
	  exit 1; \
	fi
	@printf '%s\n' \
	  "PROFILE=$(PROFILE)" \
	  "URL=$(PROFILE_URL)$(HEALTH_PATH)" \
	  "HAS_TOKEN=$$( [ -n '$(PROFILE_TOKEN)' ] && echo yes || echo no )"

cf-tunnel:
	@docker run --network host -d --name cf_hermes_profiles cloudflare/cloudflared:latest tunnel --no-autoupdate run --token ${CF_TOKEN} 
