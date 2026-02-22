# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.20.1",
# ]
# [tool.marimo.display]
# theme = "dark"
# ///

import marimo

__generated_with = "0.17.6"
app = marimo.App()


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import csv
    from math import gcd
    from typing import List, Tuple
    import io
    return List, Tuple, csv, gcd, io, mo


@app.cell(hide_code=True)
def _(List, Tuple, csv, gcd, io):
    def lcm(a: int, b: int) -> int:
        return a * b // gcd(a, b)

    def solveMods(mods: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
        period = 1
        for n, _ in mods:
            period = lcm(period, n)

        solutions = []
        for x in range(period):
            if all(x % n == r for n, r in mods):
                solutions.append(x)
        return

    def loadCsvFile(content: str) -> Tuple[Tuple[int, int], List[Tuple[int, int]]]:
        f = io.StringIO(content)
        reader = csv.reader(f)
        rows = [(int(r[0]), int(r[1])) for r in reader if r]
        if len(rows) < 2:
            raise ValueError("CSV must contain at least a target and one constraint")
        target = rows[0]
        mods = rows[1:]
        return target, mods
    return (loadCsvFile,)


@app.cell(hide_code=True)
def _(mo):
    """
    Tabs for input: Upload CSV or Manual Entry
    """
    # Manual entry UI
    manualTargetMod = mo.ui.number(value=5, start=1, label="Target modulus")
    manualTargetRem = mo.ui.number(value=2, start=0, label="Target remainder")
    manualTarget = mo.hstack([manualTargetMod, manualTargetRem])

    manualModsText = mo.ui.text_area(
        label="Constraints (one per line: modulus,remainder)",
        value="5,1\n7,3"
    )

    manualUI = mo.vstack([
        mo.md("### Format (modulus,remainder)"),
        manualTarget,
        manualModsText
    ])

    # CSV upload UI
    fileUpload = mo.ui.file(kind="area", label="Upload CSV file",filetypes=['.csv'])

    uploadUI = mo.vstack([
        mo.md("### Format (modulus,remainder)"),
        mo.md("Target: line 1"),
        mo.md("Constraints: all lines below"),
        fileUpload
    ])

    # Tabs
    selectedTab = mo.ui.tabs({
        "Upload CSV": uploadUI,
        "Manual Entry": manualUI
    })
    return (
        fileUpload,
        manualModsText,
        manualTargetMod,
        manualTargetRem,
        selectedTab,
    )


@app.cell(hide_code=True)
def _(
    fileUpload,
    loadCsvFile,
    manualModsText,
    manualTargetMod,
    manualTargetRem,
    selectedTab,
):
    # /// Definition cell — normalize inputs
    errorFlag = None
    # Target pair
    if selectedTab.value == "Manual Entry":
        targetPair = (manualTargetMod.value, manualTargetRem.value)

        # Parse constraints from textarea
        constraintPairs = []
        for line in manualModsText.value.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            try: 
                mod, rem = int(parts[0].strip()), int(parts[1].strip())
                constraintPairs.append((mod, rem))
            except Exception as e: 
                errorFlag = e
            
        
    else:
        # CSV input
        if fileUpload.value:
            targetPair, constraintPairs = loadCsvFile(fileUpload.value[0].contents)
        else:
            targetPair = None
            constraintPairs = []
    return constraintPairs, errorFlag, targetPair


@app.cell(hide_code=True)
def _(gcd):
    # /// Solver function cell (CRT-based, cycle-free)

    def solveConstraints(targetPair, constraintPairs):
        """
        Compute period, solutions, and whether the target is implied using CRT logic.
        This checks provability, not enumeration.
        Returns:
            period: LCM of all constraint moduli
            solutions: one solution modulo period (representative)
            targetImplied: True/False
        """
        if not targetPair or not constraintPairs:
            return None, False

        # Local LCM function using existing gcd
        def lcm(a, b):
            return a * b // gcd(a, b)  # gcd comes from cell-1

        # Helper: extended Euclidean algorithm
        def xgcd(a, b):
            """Return (g, x, y) such that g = gcd(a,b) = ax + by"""
            if b == 0:
                return (a, 1, 0)
            else:
                g, y, x = xgcd(b, a % b)
                y -= (a // b) * x
                return g, x, y

        # Solve CRT for constraints
        x, P = 0, 1  # initial solution x ≡ 0 mod 1
        for mi, ri in constraintPairs:
            g, s, t = xgcd(P, mi)
            if (ri - x) % g != 0:
                # No solution exists for the constraints (inconsistent)
                return None, [], False
            # Merge congruences
            x += s * (ri - x) // g * P
            P = lcm(P, mi)
            x %= P  # keep x within modulus

        period = P
        solutions = [x]  # representative solution modulo period

        # Target implied iff every solution modulo period satisfies target
        # i.e., x ≡ targetRem mod targetMod for all x ≡ solution mod period
        targetMod, targetRem = targetPair
        # check implication: x ≡ x0 (mod period) => x ≡ targetRem (mod targetMod)
        targetImplied = (x % targetMod) == targetRem and (period % targetMod) == 0

        return period, targetImplied
    return (solveConstraints,)


@app.cell(hide_code=True)
def _(
    constraintPairs,
    errorFlag,
    mo,
    selectedTab,
    solveConstraints,
    targetPair,
):
    """
    Render main UI
    """
    if not errorFlag:
        result = mo.vstack(solveConstraints(targetPair, constraintPairs))
    else:
        result = mo.md(f'error lol: {errorFlag}')
    mo.vstack([
        mo.md("# Modular Congruence Checker"),
        selectedTab,
        mo.md("---"),
        mo.md("## Result"),
        result
    ])
    return


if __name__ == "__main__":
    app.run()
