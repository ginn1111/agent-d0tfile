SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

# Repo helper targets for linking skills/plugins and creating cron jobs in Hermes profiles.

AGENTS_SKILLS_DIR ?= $(HOME)/.agents/skills
SETUP_UNIVERSAL_SKILLS := scripts/setup-universal-skills.sh
LINK_MODEL_PROVIDERS := scripts/link-model-providers.sh
LINK_HERMES_PLUGIN := scripts/link-hermes-plugin.sh
ADD_HERMES_CRON := scripts/add-hermes-cron.sh
HERMES_PROFILE_NAME ?=
PLUGIN_NAME ?=

.PHONY: help \
	universal-skills universal-skills-dry-run us us-dry-run \
	link-model-providers link-model-providers-dry-run lmp lmp-dry-run \
	link-english-tutor-plugin link-english-tutor-plugin-dry-run letp letp-dry-run \
	link-validated-mistery-loop-plugin link-validated-mistery-loop-plugin-dry-run lvmlp lvmlp-dry-run \
	add-hermes-cron add-hermes-cron-dry-run ahc ahc-dry-run

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make us / universal-skills      # link repo skills into universal agents skills folder' \
	  '  make us-dry-run                 # preview universal skill links without writing' \
	  '  make lmp / link-model-providers # link model-provider plugins into Hermes profile plugins dir' \
	  '  make lmp-dry-run                # preview model-provider plugin links without writing' \
	  '  make letp / link-english-tutor-plugin # link plugin into specific Hermes profile (defaults to picker)' \
	  '  make letp-dry-run               # preview plugin symlink without writing' \
	  '  make lvmlp / link-validated-mistery-loop-plugin # link validated-mistery-loop plugin into Hermes profile' \
	  '  make lvmlp-dry-run              # preview validated-mistery-loop plugin symlink without writing' \
	  '  make ahc / add-hermes-cron      # add repo cron jobs into Hermes profile cron/jobs.json' \
	  '  make ahc-dry-run                # preview cron job files without writing' \
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

link-english-tutor-plugin:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' PLUGIN_NAME='$(PLUGIN_NAME)' '$(LINK_HERMES_PLUGIN)' link '$(HERMES_PROFILE_NAME)' '$(PLUGIN_NAME)'

letp: link-english-tutor-plugin

link-english-tutor-plugin-dry-run:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' PLUGIN_NAME='$(PLUGIN_NAME)' '$(LINK_HERMES_PLUGIN)' list '$(HERMES_PROFILE_NAME)' '$(PLUGIN_NAME)'

letp-dry-run: link-english-tutor-plugin-dry-run

link-validated-mistery-loop-plugin:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' PLUGIN_NAME='validated-mistery-loop' '$(LINK_HERMES_PLUGIN)' link '$(HERMES_PROFILE_NAME)' 'validated-mistery-loop'

lvmlp: link-validated-mistery-loop-plugin

link-validated-mistery-loop-plugin-dry-run:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' PLUGIN_NAME='validated-mistery-loop' '$(LINK_HERMES_PLUGIN)' list '$(HERMES_PROFILE_NAME)' 'validated-mistery-loop'

lvmlp-dry-run: link-validated-mistery-loop-plugin-dry-run

add-hermes-cron:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' '$(ADD_HERMES_CRON)' add '$(HERMES_PROFILE_NAME)'

ahc: add-hermes-cron

add-hermes-cron-dry-run:
	@HERMES_PROFILE_NAME='$(HERMES_PROFILE_NAME)' '$(ADD_HERMES_CRON)' list '$(HERMES_PROFILE_NAME)'

ahc-dry-run: add-hermes-cron-dry-run

