SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

AGENTS_SKILLS_DIR ?= $(HOME)/.agents/skills
SETUP_UNIVERSAL_SKILLS := scripts/setup-universal-skills.sh

.PHONY: help universal-skills universal-skills-list

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make universal-skills      # link repo skills into universal agents skills folder' \
	  '  make universal-skills-list # preview universal skill links without writing' \
	  '' \
	  'Vars:' \
	  '  AGENTS_SKILLS_DIR=$(HOME)/.agents/skills'

universal-skills:
	@AGENTS_SKILLS_DIR='$(AGENTS_SKILLS_DIR)' '$(SETUP_UNIVERSAL_SKILLS)'

universal-skills-list:
	@AGENTS_SKILLS_DIR='$(AGENTS_SKILLS_DIR)' '$(SETUP_UNIVERSAL_SKILLS)' list
