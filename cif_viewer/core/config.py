CPK_COLORS = {
    "H": "#FFFFFF", "C": "#444444", "N": "#3050F8", "O": "#FF0D0D", "F": "#90E050",
    "Na": "#AB5CF2", "Mg": "#8AFF00", "Al": "#BFA6A6", "Si": "#F0C8A0", "P": "#FF8000",
    "S": "#FFFF30", "Cl": "#1FF01F", "Fe": "#E06633", "Cu": "#C88033", "U": "#008B8B", "Th": "#006666",
}
BASE_RADII = {"H": .35, "C": .55, "N": .55, "O": .55, "F": .50, "Na": .70, "Mg": .65, "Al": .65, "Si": .60, "U": .95, "Th": .95}

def color_for(element): return CPK_COLORS.get(element, "#CCCCCC")
def radius_for(element): return BASE_RADII.get(element, .65)
