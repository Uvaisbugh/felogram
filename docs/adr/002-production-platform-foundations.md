# ADR 002: Native upstream foundations for production

Date: 2026-10-05. Status: accepted direction; Windows choice conditional on build
verification. Supersedes ADR 001's production scope, preserving its prototype rationale.

The scope now includes everyday Windows and Android clients comparable to mature
Telegram forks. Python/TDLib remains useful for experiments, but rebuilding the
full messaging/media UI would consume effort needed for reliability and useful UX.

Use official Telegram Desktop as the preferred Windows candidate and official
Telegram Android as the Android foundation. Follow upstream directly; research
Nekogram, Forkgram, Materialgram and Unigram without combining their patch stacks.

Keep the MIT prototype intact. Create Android separately with upstream history
and license. Establish a dedicated native Windows repo after its baseline build
spike. Share product concepts/test scenarios rather than forcing a shared runtime.
Start with local, account-scoped workspace preferences.

Native builds, upstream merges, branding, signing, distribution and GPL source
obligations are maintenance work. Fork existence does not establish a working
Felogram binary. Baseline build/account verification precede customization;
public binary releases require packaging, notices and end-user checks.

Revisit Windows if a reproducible supported build, accessibility/integration or
manageable upstream merging cannot be achieved. Compare a reproduced Unigram
build and measured results before switching.
