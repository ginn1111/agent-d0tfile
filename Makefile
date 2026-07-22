SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

AGENTS_SKILLS_DIR ?= $(HOME)/.agents/skills
SETUP_UNIVERSAL_SKILLS := scripts/setup-universal-skills.sh
LINK_MODEL_PROVIDERS := scripts/link-model-providers.sh
HERMES_PROFILE_NAME ?=

.PHONY: help \
	universal-skills universal-skills-dry-run us us-dry-run \
	link-model-providers link-model-providers-dry-run lmp lmp-dry-run

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make us / universal-skills      # link repo skills into universal agents skills folder' \
	  '  make us-dry-run                 # preview universal skill links without writing' \
	  '  make lmp / link-model-providers # link model-provider plugins into Hermes profile plugins dir' \
	  '  make lmp-dry-run                # preview model-provider plugin links without writing' \
	  '' \
	  'Vars:' \
	  '  AGENTS_SKILLS_DIR=$(HOME)/.agents/skills' \
	  '  HERMES_PROFILE_NAME=<profile>'

universal-skills:
	@AGENTS_SKILLS_DIR='$(AGENTS_SKILLS_DIR)' '$(SETUP_UNIVERSAL_SKILLS)'

us: universal-skills

universal-skills-dry-run:
	@AGENTS_SKILLS_DIR='$(AGENTS_SKILLS_DIR)' '$(SETUP_UNIVERSAL_SKILLS)' list

us-dry-run: universal-skills-dry-run

link-model-providers:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' '$(LINK_MODEL_PROVIDERS)' link '$(HERMES_PROFILE_NAME)'

lmp: link-model-providers

link-model-providers-dry-run:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' '$(LINK_MODEL_PROVIDERS)' list '$(HERMES_PROFILE_NAME)'

lmp-dry-run: link-model-providers-dry-run

