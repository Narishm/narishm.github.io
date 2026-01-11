import os
import re
from PIL import Image

# =========================
# Paths (PascalCase folders)
# =========================
BaseDir = os.path.dirname(os.path.abspath(__file__))
OverlaysDir = os.path.join(BaseDir, "Overlays")
OutputDir = os.path.join(BaseDir, "Finished")

os.makedirs(OutputDir, exist_ok=True)

# Always output PNG
OutputExt = ".png"

# =========================
# Helpers
# =========================
def NaturalKey(Text: str):
    """Natural sort: 2 before 10."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", Text)]

def LoadRgba(Path: str) -> Image.Image:
    if not os.path.isfile(Path):
        raise FileNotFoundError(f"Missing file: {Path}")
    return Image.open(Path).convert("RGBA")

def SplitPrefixAndNumber(Stem: str):
    """
    Split a filename stem into (prefix, trailing_number or None)
    Example: 'ff1pr0' -> ('ff1pr', 0)
    """
    Match = re.search(r"(.*?)(\d+)$", Stem)
    if not Match:
        return Stem, None
    return Match.group(1), int(Match.group(2))

def FindBasePngInRoot():
    """
    Picks the first PNG in the script folder (natural-sorted),
    excluding anything inside Overlays/ and Finished/ (folders).
    """
    Files = []
    for Name in os.listdir(BaseDir):
        Path = os.path.join(BaseDir, Name)
        if os.path.isfile(Path) and Name.lower().endswith(".png"):
            Files.append(Name)

    Files.sort(key=NaturalKey)

    if not Files:
        raise FileNotFoundError(
            "No base PNG found next to MakeThumbs.py.\n"
            "Drop your base file here (example: ff1pr0.png)."
        )
    return Files[0]

def AlphaCompositeFullCanvas(BaseImg: Image.Image, OverlayImg: Image.Image) -> Image.Image:
    """Resize overlay to base size if needed, then alpha composite."""
    if OverlayImg.size != BaseImg.size:
        OverlayImg = OverlayImg.resize(BaseImg.size, Image.LANCZOS)
    return Image.alpha_composite(BaseImg, OverlayImg)

# =========================
# Main
# =========================
def main():
    if not os.path.isdir(OverlaysDir):
        raise FileNotFoundError(f"Missing folder: {OverlaysDir}")

    # Base (first PNG in root)
    BaseFilename = FindBasePngInRoot()
    BasePath = os.path.join(BaseDir, BaseFilename)
    BaseImg = LoadRgba(BasePath)

    Stem = os.path.splitext(BaseFilename)[0]
    Prefix, StartNum = SplitPrefixAndNumber(Stem)

    # If the base doesn't end in a number, treat it as "...0"
    if StartNum is None:
        StartNum = 0

    # Overlays (all PNGs in Overlays/)
    OverlayFiles = [f for f in os.listdir(OverlaysDir) if f.lower().endswith(".png")]
    OverlayFiles.sort(key=NaturalKey)

    if not OverlayFiles:
        raise FileNotFoundError(f"No overlay PNGs found in: {OverlaysDir}")

    Total = len(OverlayFiles)

    for Index, OverlayName in enumerate(OverlayFiles, start=1):
        OverlayPath = os.path.join(OverlaysDir, OverlayName)
        OverlayImg = LoadRgba(OverlayPath)

        OutImg = AlphaCompositeFullCanvas(BaseImg, OverlayImg)

        OutNum = StartNum + Index  # base 0 -> outputs 1..N
        OutName = f"{Prefix}{OutNum}{OutputExt}"
        OutPath = os.path.join(OutputDir, OutName)

        OutImg.save(OutPath, format="PNG")
        print(f"Generated {Index}/{Total}: {OutName}")

    print("\n✅ Done.")
    print("Base used:", BaseFilename)
    print("Output folder:", OutputDir)

if __name__ == "__main__":
    main()
