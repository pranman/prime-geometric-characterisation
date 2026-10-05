$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $repoRoot
try {
    & pdflatex -interaction=nonstopmode -halt-on-error -output-directory=paper paper/prime-geometric-characterisation.tex
    if ($LASTEXITCODE -ne 0) { throw 'First LaTeX pass failed.' }
    & bibtex paper/prime-geometric-characterisation
    if ($LASTEXITCODE -ne 0) { throw 'BibTeX failed.' }
    for ($pass = 0; $pass -lt 2; $pass++) {
        & pdflatex -interaction=nonstopmode -halt-on-error -output-directory=paper paper/prime-geometric-characterisation.tex
        if ($LASTEXITCODE -ne 0) { throw 'LaTeX cross-reference pass failed.' }
    }
} finally {
    Pop-Location
}
