class ColorPalette:
    def __init__(self, colors):
        # Allow any number of colors, but ensure we have at least 3
        if len(colors) < 3:
            raise ValueError("ColorPalette must have at least 3 colors")
        self.colors = colors

class Tableau10(ColorPalette):
    def __init__(self):
        super().__init__([
            "#4e79a7", "#f28e2b", "#e15759", "#76d7c4", "#9c755f", "#bab0ac"
        ])

class Tableau20(ColorPalette):
    def __init__(self):
        super().__init__([
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
            "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#aec7e8", "#ffbb78"
        ])

class Set1(ColorPalette):
    def __init__(self):
        super().__init__([
            "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33"
        ])

class Set2(ColorPalette):
    def __init__(self):
        super().__init__([
            "#66c2a5", "#fc8d62", "#8dd3c7", "#e6beb4", "#fdb462", "#b3b3b3"
        ])

class Set3(ColorPalette):
    def __init__(self):
        super().__init__([
            "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3", "#fdb462"
        ])
def get_all_color_palettes():
    return [
        Tableau10(),
        Tableau20(),
        Set1(),
        Set2(),
        Set3()
    ]