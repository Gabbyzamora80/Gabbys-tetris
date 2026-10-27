#!/usr/bin/env bash
set -euo pipefail

format="${1:-}"
version="${PACKAGE_VERSION:-1.0}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dist_dir="$repo_root/dist"

if [[ "$format" != "deb" && "$format" != "rpm" ]]; then
    echo "Usage: PACKAGE_VERSION=1.0 bash build-linux-package.sh {deb|rpm}" >&2
    exit 2
fi

if [[ ! "$version" =~ ^[0-9]+([.][0-9]+)*$ ]]; then
    echo "Package version must contain numbers and dots only: $version" >&2
    exit 2
fi

required_files=(
    main.py
    LICENSE
    assets/gabbys-tetris-icon.png
    data/io.github.gabbyzamora80.Gabbys-tetris.desktop
    data/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml
)
for file in "${required_files[@]}"; do
    if [[ ! -f "$repo_root/$file" ]]; then
        echo "Required project file is missing: $file" >&2
        exit 1
    fi
done

mkdir -p "$dist_dir"
work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

install_app_files() {
    local root="$1"
    install -Dm644 "$repo_root/main.py" "$root/usr/share/gabbys-tetris/main.py"
    install -Dm644 "$repo_root/LICENSE" "$root/usr/share/licenses/gabbys-tetris/LICENSE"
    install -Dm644 "$repo_root/assets/gabbys-tetris-icon.png" \
        "$root/usr/share/icons/hicolor/512x512/apps/io.github.gabbyzamora80.Gabbys-tetris.png"
    install -Dm644 "$repo_root/data/io.github.gabbyzamora80.Gabbys-tetris.desktop" \
        "$root/usr/share/applications/io.github.gabbyzamora80.Gabbys-tetris.desktop"
    install -Dm644 "$repo_root/data/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml" \
        "$root/usr/share/metainfo/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml"
}

if [[ "$format" == "deb" ]]; then
    stage="$work_dir/deb-root"
    install_app_files "$stage"
    install -d "$stage/DEBIAN"
    cat > "$stage/DEBIAN/control" <<EOF
Package: gabbys-tetris
Version: ${version}-1
Section: games
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-tk, python3-pygame
Maintainer: Gabby Zamora
Description: A falling-block game with chiptune music
 A colorful Tetris-style game with a welcome screen, keyboard controls,
 chiptune music, sound effects, score, lines, and levels.
EOF
    cat > "$stage/usr/bin/gabbys-tetris" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/share/gabbys-tetris/main.py "$@"
EOF
    chmod 0755 "$stage/usr/bin/gabbys-tetris"
    dpkg-deb --build --root-owner-group "$stage" \
        "$dist_dir/gabbys-tetris_${version}-1_all.deb"
    echo "Created $dist_dir/gabbys-tetris_${version}-1_all.deb"
    exit 0
fi

topdir="$work_dir/rpmbuild"
mkdir -p "$topdir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
tar --create --gzip --file "$topdir/SOURCES/gabbys-tetris-${version}.tar.gz" \
    --directory="$repo_root" --transform="s,^,gabbys-tetris-${version}/," \
    main.py LICENSE assets/gabbys-tetris-icon.png \
    data/io.github.gabbyzamora80.Gabbys-tetris.desktop \
    data/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml
cat > "$topdir/SPECS/gabbys-tetris.spec" <<'SPEC'
Name:           gabbys-tetris
Version:        @VERSION@
Release:        1%{?dist}
Summary:        A falling-block game with chiptune music
License:        GPL-3.0-only
URL:            https://github.com/Gabbyzamora80/Gabbys-tetris
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.10
Requires:       python3-tkinter
Requires:       python3-pygame

%description
A colorful Tetris-style game with a welcome screen, keyboard controls,
chiptune music, sound effects, score, lines, and levels.

%prep
%setup -q

%build

%install
install -Dm644 main.py %{buildroot}%{_datadir}/gabbys-tetris/main.py
install -Dm644 LICENSE %{buildroot}%{_datadir}/licenses/gabbys-tetris/LICENSE
install -Dm644 assets/gabbys-tetris-icon.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/io.github.gabbyzamora80.Gabbys-tetris.png
install -Dm644 data/io.github.gabbyzamora80.Gabbys-tetris.desktop %{buildroot}%{_datadir}/applications/io.github.gabbyzamora80.Gabbys-tetris.desktop
install -Dm644 data/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml %{buildroot}%{_datadir}/metainfo/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/gabbys-tetris <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/share/gabbys-tetris/main.py "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/gabbys-tetris

%files
%license LICENSE
%{_bindir}/gabbys-tetris
%{_datadir}/gabbys-tetris/main.py
%{_datadir}/applications/io.github.gabbyzamora80.Gabbys-tetris.desktop
%{_datadir}/icons/hicolor/512x512/apps/io.github.gabbyzamora80.Gabbys-tetris.png
%{_datadir}/metainfo/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml

SPEC
sed "s/@VERSION@/${version}/g" "$topdir/SPECS/gabbys-tetris.spec" \
    > "$topdir/SPECS/gabbys-tetris.spec.tmp"
mv "$topdir/SPECS/gabbys-tetris.spec.tmp" "$topdir/SPECS/gabbys-tetris.spec"
rpmbuild --define "_topdir $topdir" -bb "$topdir/SPECS/gabbys-tetris.spec"
cp "$topdir"/RPMS/noarch/gabbys-tetris-"$version"-1*.noarch.rpm "$dist_dir/"
echo "Created $dist_dir/gabbys-tetris-${version}-1*.noarch.rpm"
