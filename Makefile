SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

INSTALL_HERMES_PLUGIN := scripts/install_hermes_plugin.py
SETUP_UNIVERSAL_SKILLS := scripts/setup-universal-skills.sh
ADD_HERMES_CRON := scripts/add-hermes-cron.sh
INSTALL_THEME_CINDY := scripts/install_theme_cindy.py
INSTALL_WORKSPACE_FONT := scripts/install_workspace_font.py
KANBAN_TUI_MANIFEST := tools/herdr/plugins/hermes-kanban/Cargo.toml

AGENTS_SKILLS_DIR ?= $(HOME)/.agents/skills
HERMES_PROFILE_NAME ?=
PROFILE ?= $(HERMES_PROFILE_NAME)
PLUGIN ?=

.PHONY: help test \
	hermes-plugin-list hpl \
	hermes-plugin-install hpi \
	hermes-plugin-install-dry-run hpi-dry-run \
	hermes-plugin-uninstall hpu \
	universal-skills universal-skills-dry-run us us-dry-run \
	add-hermes-cron add-hermes-cron-dry-run ahc ahc-dry-run \
	theme-cindy theme-cindy-dry-run theme-cindy-restore theme-cindy-restore-dry-run \
	workspace-font workspace-font-dry-run workspace-font-restore workspace-font-restore-dry-run \
	wsf wsf-dry-run wsf-restore wsf-restore-dry-run \
	herdr-kanban-build hkb herdr-kanban-build-dry-run hkb-dry-run

help:
	@printf '%s\n' \
	  'Targets:' \
	  '  make test                                # run repo unit tests' \
	  '  make hpl / hermes-plugin-list            # list repo Hermes plugins & profiles' \
	  '  make hpi / hermes-plugin-install         # install PLUGIN=<name> into PROFILE=<name>' \
	  '  make hpi-dry-run                         # preview plugin install without writing' \
	  '  make hpu / hermes-plugin-uninstall       # remove PLUGIN=<name> from PROFILE=<name>' \
	  '  make us / universal-skills               # link repo skills into ~/.agents/skills' \
	  '  make us-dry-run                          # preview universal skill links' \
	  '  make ahc / add-hermes-cron               # add repo cron jobs into Hermes profile' \
	  '  make ahc-dry-run                         # preview cron job files' \
	  '  make theme-cindy                         # link cindy theme into ~/.config + profiles' \
	  '  make theme-cindy-dry-run                 # preview theme links/edits' \
	  '  make theme-cindy-restore                 # restore pre-cindy backups' \
	  '  make wsf / workspace-font                # install Terminess Nerd Font for workspace' \
	  '  make wsf-dry-run                         # preview font install/edits' \
	  '  make wsf-restore                         # restore pre-wsfont backups' \
	  '  make hkb / herdr-kanban-build            # build native Herdr Kanban TUI (Cargo)' \
	  '' \
	  'Vars:' \
	  '  PLUGIN=$(PLUGIN)  PROFILE=<profile>  AGENTS_SKILLS_DIR=$(AGENTS_SKILLS_DIR)'

test:
	@python3 -m unittest discover -s tests -p "test_*.py" -v

hermes-plugin-list:
	@python3 '$(INSTALL_HERMES_PLUGIN)' list

hpl: hermes-plugin-list

hermes-plugin-install:
	@python3 '$(INSTALL_HERMES_PLUGIN)' install $(if $(PLUGIN),'$(PLUGIN)',) $(if $(PROFILE),--profile '$(PROFILE)',)

hpi: hermes-plugin-install

hermes-plugin-install-dry-run:
	@python3 '$(INSTALL_HERMES_PLUGIN)' install $(if $(PLUGIN),'$(PLUGIN)',) $(if $(PROFILE),--profile '$(PROFILE)',) --dry-run

hpi-dry-run: hermes-plugin-install-dry-run

hermes-plugin-uninstall:
	@python3 '$(INSTALL_HERMES_PLUGIN)' uninstall $(if $(PLUGIN),'$(PLUGIN)',) $(if $(PROFILE),--profile '$(PROFILE)',)

hpu: hermes-plugin-uninstall

universal-skills:
	@AGENTS_SKILLS_DIR='$(AGENTS_SKILLS_DIR)' '$(SETUP_UNIVERSAL_SKILLS)'

us: universal-skills

universal-skills-dry-run:
	@AGENTS_SKILLS_DIR='$(AGENTS_SKILLS_DIR)' '$(SETUP_UNIVERSAL_SKILLS)' list

us-dry-run: universal-skills-dry-run

add-hermes-cron:
	@HERMES_PROFILE_NAME='$(PROFILE)' '$(ADD_HERMES_CRON)' add '$(PROFILE)'

ahc: add-hermes-cron

add-hermes-cron-dry-run:
	@HERMES_PROFILE_NAME='$(PROFILE)' '$(ADD_HERMES_CRON)' list '$(PROFILE)'

ahc-dry-run: add-hermes-cron-dry-run

theme-cindy:
	@python3 '$(INSTALL_THEME_CINDY)'

theme-cindy-dry-run:
	@python3 '$(INSTALL_THEME_CINDY)' --dry-run

theme-cindy-restore:
	@python3 '$(INSTALL_THEME_CINDY)' --restore

theme-cindy-restore-dry-run:
	@python3 '$(INSTALL_THEME_CINDY)' --restore --dry-run

workspace-font:
	@python3 '$(INSTALL_WORKSPACE_FONT)'

wsf: workspace-font

workspace-font-dry-run:
	@python3 '$(INSTALL_WORKSPACE_FONT)' --dry-run

wsf-dry-run: workspace-font-dry-run

workspace-font-restore:
	@python3 '$(INSTALL_WORKSPACE_FONT)' --restore

wsf-restore: workspace-font-restore

workspace-font-restore-dry-run:
	@python3 '$(INSTALL_WORKSPACE_FONT)' --restore --dry-run

wsf-restore-dry-run: workspace-font-restore-dry-run

herdr-kanban-build:
	@cargo build --release --locked --manifest-path '$(KANBAN_TUI_MANIFEST)'

hkb: herdr-kanban-build

herdr-kanban-build-dry-run:
	@printf '%s\n' 'cargo build --release --locked --manifest-path $(KANBAN_TUI_MANIFEST)'

hkb-dry-run: herdr-kanban-build-dry-run
