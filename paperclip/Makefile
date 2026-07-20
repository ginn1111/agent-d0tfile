
.PHONY: onboard start bootstrap-ceo tunnel-start

include .env
export

onboard:
	@pnpm dlx paperclipai onboard --yes

bootstrap-ceo:
	@pnpm dlx paperclipai auth bootstrap-ceo

tunnel-start:
	@docker compose up -d cloudflared_paperclip

start: tunnel-start
	@docker compose up -d
	@pnpm dlx paperclipai run
