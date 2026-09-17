TERMUX_PKG_HOMEPAGE=https://github.com/lost-rob0t/starintel-gpt-auto-dig
TERMUX_PKG_DESCRIPTION="StarIntel authenticated bulk ingest client"
TERMUX_PKG_LICENSE="GPL-3.0-or-later"
TERMUX_PKG_MAINTAINER="@lost-rob0t"
TERMUX_PKG_VERSION=0.9.1
TERMUX_PKG_DEPENDS="ca-certificates, libandroid-glob, libandroid-spawn, openssl"
TERMUX_PKG_SKIP_SRC_EXTRACT=true

termux_step_make() {
	termux_setup_nim

	local nim_arch="$TERMUX_ARCH"
	case "$TERMUX_ARCH" in
		aarch64) nim_arch=arm64 ;;
		i686) nim_arch=i386 ;;
		x86_64) nim_arch=amd64 ;;
	esac

	local nim_ldflags="$LDFLAGS -landroid-glob -landroid-spawn"

	mkdir -p "$TERMUX_PKG_BUILDDIR/bin"

	nim \
		--cc:clang \
		--clang.exe="$CC" \
		--clang.linkerexe="$CC" \
		--cpu:"$nim_arch" \
		--define:termux \
		--os:android \
		-d:"tempDir:$TERMUX_PREFIX/tmp" \
		-d:release \
		-d:ssl \
		-d:sslVersion=3 \
		--opt:speed \
		--mm:orc \
		--threads:on \
		-l:"$nim_ldflags" \
		-t:"$CPPFLAGS $CFLAGS" \
		--out:"$TERMUX_PKG_BUILDDIR/bin/starintel-ingest" \
		c "$TERMUX_PKG_BUILDER_DIR/starintel_ingest_core.nim"
}

termux_step_make_install() {
	install -Dm700 \
		"$TERMUX_PKG_BUILDDIR/bin/starintel-ingest" \
		"$TERMUX_PREFIX/bin/starintel-ingest"

	ln -sfr \
		"$TERMUX_PREFIX/bin/starintel-ingest" \
		"$TERMUX_PREFIX/bin/starintel-ingest-core"

	install -Dm600 \
		"$TERMUX_PKG_BUILDER_DIR/README.termux.md" \
		"$TERMUX_PREFIX/share/doc/starintel-ingest/README.md"
}
