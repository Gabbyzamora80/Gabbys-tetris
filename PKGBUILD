pkgname=gabbys-tetris
pkgver=1.0
pkgrel=1
pkgdesc="Gabby's Tetris, a falling-block game with chiptune music"
arch=('any')
url="https://github.com/Gabbyzamora80/Gabbys-tetris"
license=('GPL3')
depends=('python>=3.10' 'tk' 'python-pygame')
source=()
sha256sums=()

package() {
    install -Dm644 "$startdir/main.py" \
        "$pkgdir/usr/share/gabbys-tetris/main.py"
    install -Dm644 "$startdir/LICENSE" \
        "$pkgdir/usr/share/licenses/gabbys-tetris/LICENSE"
    install -Dm644 "$startdir/assets/gabbys-tetris-icon.png" \
        "$pkgdir/usr/share/icons/hicolor/512x512/apps/io.github.gabbyzamora80.Gabbys-tetris.png"
    install -Dm644 "$startdir/data/io.github.gabbyzamora80.Gabbys-tetris.desktop" \
        "$pkgdir/usr/share/applications/io.github.gabbyzamora80.Gabbys-tetris.desktop"
    install -Dm644 "$startdir/data/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml" \
        "$pkgdir/usr/share/metainfo/io.github.gabbyzamora80.Gabbys-tetris.metainfo.xml"

    install -d "$pkgdir/usr/bin"
    cat > "$pkgdir/usr/bin/gabbys-tetris" <<'EOF'
#!/bin/sh
exec /usr/bin/python /usr/share/gabbys-tetris/main.py "$@"
EOF
    chmod 0755 "$pkgdir/usr/bin/gabbys-tetris"
}
