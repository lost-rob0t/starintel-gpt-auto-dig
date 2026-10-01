#!/usr/bin/env bash
set -euo pipefail

fail() {
	printf 'starintel-ingest installer: %s\n' "$*" >&2
	exit 1
}

command -v dpkg >/dev/null 2>&1 || fail "dpkg is required; run this inside Termux"
command -v apt >/dev/null 2>&1 || fail "apt is required; run this inside Termux"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum is required"

bundle_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$bundle_dir"

test -f SHA256SUMS || fail "SHA256SUMS is missing from the bundle"
sha256sum -c SHA256SUMS

host_arch="$(dpkg --print-architecture)"
case "$host_arch" in
	aarch64|arm|i686|x86_64)
		termux_arch="$host_arch"
		;;
	arm64)
		termux_arch=aarch64
		;;
	armhf|armel)
		termux_arch=arm
		;;
	i386)
		termux_arch=i686
		;;
	amd64)
		termux_arch=x86_64
		;;
	*)
		fail "unsupported architecture: $host_arch"
		;;
esac

shopt -s nullglob
packages=(starintel-ingest_*_"$termux_arch".deb)
if (( ${#packages[@]} != 1 )); then
	fail "expected exactly one package for $termux_arch, found ${#packages[@]}"
fi

printf 'Installing %s for %s...\n' "${packages[0]}" "$termux_arch"
apt install -y "./${packages[0]}"
printf 'Installed. Run: starintel-ingest --help\n'
