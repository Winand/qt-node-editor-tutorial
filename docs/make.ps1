param (
    [switch]$clean
)
if($clean) {
    rm -R -ErrorAction SilentlyContinue $PSScriptRoot/source/apidoc  # clean apidoc generated files
    sphinx-build -M clean $PSScriptRoot/source $PSScriptRoot/build
} else {
    $src_dir="$PSScriptRoot/source"
    # Run apidoc manually, because sphinx.ext.apidoc does not use custom template dir
    # https://github.com/sphinx-doc/sphinx/blob/v8.2.3/sphinx/ext/apidoc/_extension.py
    # Options: -e file per module, -T do not create toc (modules.rst), -t custom templates
    sphinx-apidoc -e -T -t $src_dir/_templates/apidoc -o $src_dir/apidoc $PSScriptRoot/../src/qt_node_editor
    sphinx-build $src_dir $PSScriptRoot/build
    # sphinx-build -b coverage $src_dir $PSScriptRoot/build
}
